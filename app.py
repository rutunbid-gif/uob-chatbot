from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import os
from pathlib import Path
import re
import json
import csv
from io import StringIO, BytesIO

# RAG Components
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

app = Flask(__name__)

# Global variables
vectorstore = None
qa_chain = None
conversations = {}
conversation_memories = {}
analytics = {
    'total_queries': 0,
    'languages': {},
    'ratings': {'up': 0, 'down': 0},
    'response_times': [],
    'common_queries': {}
}

def initialize_rag_system():
    """Initialize the RAG system"""
    global vectorstore, qa_chain
    
    print("🔧 Initializing Enhanced RAG system...")
    
    datasets_path = Path("datasets")
    if not datasets_path.exists():
        print("❌ Error: 'datasets' folder not found!")
        return False
    
    print(f"📂 Loading PDFs from: {datasets_path}")
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
        print("❌ No PDF documents found!")
        return False
    
    print("✂️  Splitting documents...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=300,
        length_function=len
    )
    texts = text_splitter.split_documents(documents)
    print(f"✅ Created {len(texts)} text chunks")
    
    print("🧮 Creating multilingual embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    print("💾 Building vector database...")
    vectorstore = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    print("✅ Vector database created")
    
    print("🤖 Connecting to Ollama...")
    try:
        llm = Ollama(model="llama3.2", temperature=0.2)
        print("✅ Connected to Ollama")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    prompt_template = """You are a helpful University of Bristol AI assistant. Respond in the SAME language the student uses.

INSTRUCTIONS:
1. Answer in the same language as the question
2. Be conversational and friendly
3. Give specific information from context
4. Use bullet points for multiple items
5. If unclear, ask "Did you mean...?" and suggest alternatives
6. Only use information from context
7. If not in context, say "I don't have that information" and suggest contacting relevant service
8. Always cite sources

Context:
{context}

Question: {question}

Response (same language):"""

    PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "fetch_k": 10}
        ),
        chain_type_kwargs={"prompt": PROMPT},
        return_source_documents=True
    )
    
    print("✅ RAG system ready with all features!")
    return True

def detect_language(text):
    """Detect language of input"""
    if re.search(r'[\u4e00-\u9fff]', text):
        return 'Chinese'
    if re.search(r'[\u0600-\u06ff]', text):
        return 'Arabic'
    spanish_words = ['qué', 'cómo', 'dónde', 'cuándo', 'por favor']
    if any(word in text.lower() for word in spanish_words):
        return 'Spanish'
    return 'English'

def get_suggested_questions(user_query, bot_response):
    """Generate suggested follow-up questions"""
    query_lower = user_query.lower()
    
    suggestions = []
    
    # Course-related suggestions
    if any(word in query_lower for word in ['course', 'program', 'degree', 'study', '课程']):
        suggestions = [
            "What are the tuition fees?",
            "When does the course start?",
            "What are the entry requirements?"
        ]
    
    # Accommodation suggestions
    elif any(word in query_lower for word in ['accommodation', 'housing', 'room', 'hall', '住宿']):
        suggestions = [
            "What facilities are available?",
            "How do I apply for accommodation?",
            "What are the cheapest options?"
        ]
    
    # Scholarship suggestions
    elif any(word in query_lower for word in ['scholarship', 'funding', 'bursary', 'financial', '奖学金']):
        suggestions = [
            "What documents do I need?",
            "When is the application deadline?",
            "Am I eligible for funding?"
        ]
    
    # Extension suggestions
    elif any(word in query_lower for word in ['extension', 'deadline', 'ec', 'exceptional']):
        suggestions = [
            "What evidence do I need?",
            "How do I submit the form?",
            "Can I appeal if rejected?"
        ]
    
    # General suggestions
    else:
        suggestions = [
            "Tell me about scholarships",
            "What accommodation is available?",
            "How do I contact student services?"
        ]
    
    return suggestions[:3]  # Return max 3

def log_analytics(query, language, response_time, rating=None):
    """Log analytics data"""
    analytics['total_queries'] += 1
    
    # Track language
    analytics['languages'][language] = analytics['languages'].get(language, 0) + 1
    
    # Track response time
    analytics['response_times'].append(response_time)
    
    # Track common queries
    query_key = query.lower()[:50]
    analytics['common_queries'][query_key] = analytics['common_queries'].get(query_key, 0) + 1
    
    # Track ratings
    if rating:
        analytics['ratings'][rating] = analytics['ratings'].get(rating, 0) + 1

@app.route('/')
def home():
   return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    global qa_chain
    
    start_time = datetime.now()
    
    try:
        if qa_chain is None:
            return jsonify({
                'error': 'System not ready. Please wait or refresh the page.',
                'status': 'error',
                'suggestions': ['Try again in a moment', 'Check server logs', 'Contact support']
            }), 500
        
        data = request.json
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id', 'default')
        
        if not user_message:
            return jsonify({'error': 'Please type a question'}), 400
        
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        
        detected_lang = detect_language(user_message)
        
        # Store user message
        conversations[conversation_id].append({
            'role': 'user',
            'message': user_message,
            'language': detected_lang,
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"🔍 Query: {user_message[:50]}... (Language: {detected_lang})")
        
        # Get RAG response
        result = qa_chain.invoke({"query": user_message})
        bot_response = result['result']
        source_docs = result['source_documents']
        
        # Format sources
        if source_docs:
            sources = []
            seen = set()
            for doc in source_docs:
                source_file = Path(doc.metadata.get('source', '')).name
                clean_name = source_file.replace('_', ' ').replace('.pdf', '')
                if clean_name and clean_name not in seen:
                    sources.append(clean_name)
                    seen.add(clean_name)
            
            if sources:
                source_labels = {
                    'Chinese': '**来源：**',
                    'Arabic': '**المصادر:**',
                    'Spanish': '**Fuentes:**',
                    'English': '**Sources:**'
                }
                label = source_labels.get(detected_lang, '**Sources:**')
                source_text = f"\n\n{label}\n" + '\n'.join([f"  • {s}" for s in sources[:3]])
                bot_response += source_text
        
        # Get suggested questions
        suggestions = get_suggested_questions(user_message, bot_response)
        
        # Calculate response time
        response_time = (datetime.now() - start_time).total_seconds()
        
        # Log analytics
        log_analytics(user_message, detected_lang, response_time)
        
        # Store bot response
        conversations[conversation_id].append({
            'role': 'bot',
            'message': bot_response,
            'suggestions': suggestions,
            'timestamp': datetime.now().isoformat(),
            'response_time': response_time
        })
        
        return jsonify({
            'response': bot_response,
            'suggestions': suggestions,
            'language': detected_lang,
            'response_time': round(response_time, 2),
            'status': 'success'
        })
    
    except Exception as e:
        print(f"❌ Error: {e}")
        
        error_messages = {
            'English': "I'm having trouble answering that. Could you rephrase your question?",
            'Chinese': "抱歉，我无法回答。您能换个方式问吗？",
            'Spanish': "No puedo responder eso. ¿Podrías reformular?",
            'Arabic': "لا أستطيع الإجابة. هل يمكنك إعادة الصياغة؟"
        }
        
        detected_lang = detect_language(data.get('message', ''))
        error_msg = error_messages.get(detected_lang, error_messages['English'])
        
        return jsonify({
            'response': error_msg,
            'suggestions': ['Try a simpler question', 'Ask about courses or accommodation', 'Contact student services'],
            'status': 'error'
        }), 200

@app.route('/api/feedback', methods=['POST'])
def feedback():
    """Handle user ratings"""
    data = request.json
    conversation_id = data.get('conversation_id')
    message_index = data.get('message_index')
    rating = data.get('rating')  # 'up' or 'down'
    
    analytics['ratings'][rating] = analytics['ratings'].get(rating, 0) + 1
    
    print(f"📊 Feedback: {rating} for message #{message_index}")
    
    return jsonify({'status': 'success', 'message': 'Thank you for your feedback!'})

@app.route('/api/export/<conversation_id>', methods=['GET'])
def export_conversation(conversation_id):
    """Export conversation as text file"""
    history = conversations.get(conversation_id, [])
    
    if not history:
        return jsonify({'error': 'No conversation found'}), 404
    
    # Create text format
    output = StringIO()
    output.write("University of Bristol Chatbot Conversation\n")
    output.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    output.write("=" * 60 + "\n\n")
    
    for msg in history:
        role = "You" if msg['role'] == 'user' else "Bot"
        timestamp = msg.get('timestamp', '')
        message = msg.get('message', '')
        output.write(f"[{role}] {timestamp}\n{message}\n\n")
    
    output.write("=" * 60 + "\n")
    output.write("Generated by UoB AI Chatbot\n")
    
    # Convert to bytes
    output.seek(0)
    byte_output = BytesIO(output.getvalue().encode('utf-8'))
    byte_output.seek(0)
    
    return send_file(
        byte_output,
        mimetype='text/plain',
        as_attachment=True,
        download_name=f'chat_export_{conversation_id}_{datetime.now().strftime("%Y%m%d")}.txt'
    )

@app.route('/api/history/<conversation_id>', methods=['GET'])
def get_history(conversation_id):
    """Get conversation history"""
    history = conversations.get(conversation_id, [])
    return jsonify({'history': history})

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get analytics data"""
    avg_response_time = sum(analytics['response_times']) / len(analytics['response_times']) if analytics['response_times'] else 0
    
    # Get top queries
    top_queries = sorted(analytics['common_queries'].items(), key=lambda x: x[1], reverse=True)[:5]
    
    return jsonify({
        'total_queries': analytics['total_queries'],
        'languages': analytics['languages'],
        'ratings': analytics['ratings'],
        'avg_response_time': round(avg_response_time, 2),
        'top_queries': [{'query': q, 'count': c} for q, c in top_queries],
        'satisfaction_rate': round((analytics['ratings'].get('up', 0) / max(sum(analytics['ratings'].values()), 1)) * 100, 1)
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy' if qa_chain is not None else 'initializing',
        'timestamp': datetime.now().isoformat(),
        'features': {
            'multilingual': True,
            'context_aware': True,
            'suggestions': True,
            'export': True,
            'analytics': True,
            'ratings': True
        }
    })

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 University of Bristol Enhanced AI Chatbot")
    print("=" * 70)
    
    success = initialize_rag_system()
    
    if not success:
        print("\n❌ Failed to initialize")
        exit(1)
    
    print("\n" + "=" * 70)
    print("✨ Features:")
    print("   🌍 Multilingual (Chinese, Spanish, Arabic, etc.)")
    print("   💡 Smart suggestions")
    print("   ⭐ Response ratings")
    print("   📄 Export conversations")
    print("   📊 Analytics tracking")
    print("   📱 Mobile responsive")
    print("\n📍 Open: http://localhost:5000")
    print("⚠️  Press CTRL+C to stop")
    print("=" * 70 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000)