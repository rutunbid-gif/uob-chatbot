from flask import Flask, render_template, request, jsonify
from datetime import datetime
import os
from pathlib import Path

# RAG Components
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

app = Flask(__name__)

# Global variables for RAG system
vectorstore = None
qa_chain = None
conversations = {}

def initialize_rag_system():
    """Initialize the RAG system with PDF documents"""
    global vectorstore, qa_chain
    
    print("🔧 Initializing RAG system...")
    
    # 1. Load PDFs from datasets folder
    datasets_path = Path("datasets")
    if not datasets_path.exists():
        print("❌ Error: 'datasets' folder not found!")
        print("Please create a 'datasets' folder and add your PDF files.")
        return False
    
    print(f"📂 Loading PDFs from: {datasets_path}")
    
    # Load all PDFs
    loader = DirectoryLoader(
        str(datasets_path),
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=True
    )
    
    try:
        documents = loader.load()
        print(f"✅ Loaded {len(documents)} pages from PDFs")
    except Exception as e:
        print(f"❌ Error loading PDFs: {e}")
        return False
    
    if len(documents) == 0:
        print("❌ No PDF documents found in datasets folder!")
        return False
    
    # 2. Split documents into chunks (increased size for better context)
    print("✂️  Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,  # Increased from 1000
        chunk_overlap=300,  # Increased from 200
        length_function=len
    )
    texts = text_splitter.split_documents(documents)
    print(f"✅ Created {len(texts)} text chunks")
    
    # 3. Create embeddings
    print("🧮 Creating embeddings (this may take a minute)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    # 4. Create vector store
    print("💾 Building vector database...")
    vectorstore = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    print("✅ Vector database created")
    
    # 5. Initialize Ollama LLM
    print("🤖 Connecting to Ollama...")
    try:
        llm = Ollama(
            model="llama3.2",
            temperature=0.1  # Very low = more factual responses
        )
        print("✅ Connected to Ollama")
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        print("Make sure Ollama is running: ollama serve")
        return False
    
    # 6. Create custom prompt template
    prompt_template = """You are a University of Bristol student information assistant. Answer questions using ONLY the information provided in the context below.

RULES:
1. Answer directly and concisely
2. Extract specific facts: numbers, dates, names, fees
3. If multiple items match, list them clearly
4. If information is not in the context, say: "I don't have that specific information in my database"
5. Do NOT make assumptions or add information not in the context
6. Be helpful and student-friendly

Context:
{context}

Student Question: {question}

Answer:"""

    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )
    
    # 7. Create QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(
            search_kwargs={"k": 5}  # Retrieve top 5 chunks for better context
        ),
        chain_type_kwargs={"prompt": PROMPT},
        return_source_documents=True
    )
    
    print("✅ RAG system ready!")
    return True

@app.route('/')
def home():
    """Render the main chat interface"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with RAG"""
    global qa_chain
    
    try:
        if qa_chain is None:
            return jsonify({
                'error': 'RAG system not initialized. Please check server logs.',
                'status': 'error'
            }), 500
        
        data = request.json
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id', 'default')
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Initialize conversation history
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        
        # Store user message
        conversations[conversation_id].append({
            'role': 'user',
            'message': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Get response from RAG system
        print(f"🔍 Processing query: {user_message}")
        result = qa_chain.invoke({"query": user_message})
        
        bot_response = result['result']
        source_docs = result['source_documents']
        
        # Add source information (cleaner format for dissertation)
        if source_docs:
            sources = []
            for doc in source_docs:
                source = doc.metadata.get('source', 'Unknown')
                source_file = Path(source).name
                # Clean up the filename for display
                clean_name = source_file.replace('_', ' ').replace('.pdf', '')
                if clean_name not in sources:
                    sources.append(clean_name)
            
            if sources:
                # Format sources nicely
                source_list = '\n'.join([f"  • {s}" for s in sources[:3]])  # Show max 3 sources
                bot_response += f"\n\n**Sources:**\n{source_list}"
        
        # Store bot response
        conversations[conversation_id].append({
            'role': 'bot',
            'message': bot_response,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'response': bot_response,
            'status': 'success'
        })
    
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        return jsonify({
            'error': f'Error processing your question: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/api/history/<conversation_id>', methods=['GET'])
def get_history(conversation_id):
    """Get conversation history"""
    history = conversations.get(conversation_id, [])
    return jsonify({'history': history})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy' if qa_chain is not None else 'not_initialized',
        'timestamp': datetime.now().isoformat(),
        'rag_enabled': qa_chain is not None
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🎓 University of Bristol RAG Chatbot")
    print("=" * 60)
    
    # Initialize RAG system
    success = initialize_rag_system()
    
    if not success:
        print("\n❌ Failed to initialize RAG system")
        print("Please check the error messages above and fix the issues.")
        exit(1)
    
    print("\n" + "=" * 60)
    print("🚀 Starting Flask server...")
    print("📍 Open your browser: http://localhost:5000")
    print("⚠️  Press CTRL+C to stop")
    print("=" * 60 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000)