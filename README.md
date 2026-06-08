# 🤖 Agentic AI - Learning Repository

A comprehensive learning repository exploring Agentic AI, LangChain, LangGraph, RAG, Vector Databases, and Multi-modal AI applications.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.12-green.svg)](https://python.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.53-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40.1-red.svg)](https://streamlit.io/)

---

## 📂 Repository Structure

```
agenticAI/
├── project1/          🏆 Featured Production App
├── example1/          📚 Learning Examples
├── simplecall/        🔰 Basic LLM Calls
├── ragbasics/         📖 RAG Fundamentals
├── vector_db/         🗄️ Vector Database Basics
├── multimodel/        🖼️ Multi-modal AI
└── README.md          📄 This file
```

---

## 🏆 Featured Project: ShopWise AI

### **Production-Ready AI Shopping Assistant**

A complete, deployable intelligent shopping platform featuring semantic search, visual product discovery, and natural language ordering.

**🔗 Live Demo:** [Deploy on Streamlit Cloud](#deployment)

**📍 Location:** [`project1/`](./project1/)

### **Key Features:**
- 🤖 **LangGraph Agent** - ReAct agent with tool calling
- 🔍 **Semantic Search** - Vector similarity using sentence transformers
- 🖼️ **Visual Search** - Upload images to find similar products
- 💳 **Smart Checkout** - Natural language ordering
- 🔐 **User Authentication** - Secure login with bcrypt
- 📊 **Personalization** - Search history and recommendations
- 🎨 **Premium UI** - Luxury editorial design (Linear.app inspired)

### **Technology Stack:**
```
AI/ML:          LangGraph, LangChain, Sentence Transformers
Database:       SQLite, ChromaDB (vector embeddings)
LLM Provider:   GROQ (Qwen-3-32B, Llama-4-Scout)
Frontend:       Streamlit
Auth:           bcrypt, session tokens
```

### **Quick Start:**
```bash
cd project1
pip install -r requirements.txt
streamlit run app.py
```

**📖 Full Documentation:** [project1/README.md](./project1/README.md)

---

## 📚 Learning Projects

### **example1/** - Basic Shopping Agent
Early prototype demonstrating core agent concepts.

**Focus:**
- Basic LangChain agent setup
- Simple tool calling
- Product search and ordering

### **simplecall/** - LLM Call Basics
Jupyter notebook exploring basic LLM interactions.

**Topics:**
- Direct API calls to LLMs
- Prompt engineering
- Response parsing

### **ragbasics/** - Retrieval Augmented Generation
Introduction to RAG patterns using PDF documents.

**Concepts:**
- Document loading and chunking
- Embedding generation
- Similarity search
- Context injection

**Includes:**
- `rag.ipynb` - RAG implementation notebook
- `telecom_guide.pdf` - Sample document

### **vector_db/** - Vector Database Fundamentals
Exploring vector storage and similarity search.

**Topics:**
- Vector embeddings
- ChromaDB basics
- Similarity metrics
- Query optimization

### **multimodel/** - Multi-modal AI
Working with vision-language models.

**Examples:**
- Image analysis
- Blood work interpretation (demo)
- Vision + text integration

---

## 🚀 Deployment Guide

### **Deploy ShopWise AI to Streamlit Cloud**

**Step 1: Push to GitHub** (Already done! ✅)
```bash
git push origin main
```

**Step 2: Configure Streamlit Cloud**
1. Go to [share.streamlit.io](https://share.streamlit.io/)
2. Click "New app"
3. Select this repository
4. Set main file path: `project1/app.py`
5. Add secrets:
   ```toml
   GROQ_API_KEY = "your_groq_api_key_here"
   ```

**Step 3: Deploy!**

First deployment takes ~90 seconds (includes model download and database setup).

**📖 Detailed Guide:** [project1/DEPLOYMENT.md](./project1/DEPLOYMENT.md)

---

## 🛠️ Technologies Used

### **AI/ML Frameworks**
- **LangChain** - Agent orchestration and tool calling
- **LangGraph** - Stateful agent workflows
- **Sentence Transformers** - Semantic embeddings
- **GROQ** - Fast LLM inference

### **Databases**
- **SQLite** - Relational data (products, users, orders)
- **ChromaDB** - Vector embeddings for semantic search

### **Web Frameworks**
- **Streamlit** - Rapid UI development
- **Python 3.11+** - Modern Python features

### **Authentication**
- **bcrypt** - Secure password hashing
- **Session tokens** - Stateful authentication

---

## 📖 Learning Path

### **1. Start with Basics**
```bash
cd simplecall
jupyter notebook call_llm.ipynb
```

### **2. Explore RAG**
```bash
cd ragbasics
jupyter notebook rag.ipynb
```

### **3. Vector Databases**
```bash
cd vector_db
jupyter notebook vectordb1.ipynb
```

### **4. Multi-modal AI**
```bash
cd multimodel
jupyter notebook multimodal_demo.ipynb
```

### **5. Production App**
```bash
cd project1
streamlit run app.py
```

---

## 🔧 Setup & Installation

### **Prerequisites**
- Python 3.11 or higher
- pip package manager
- Git

### **Clone Repository**
```bash
git clone https://github.com/annamalai199/ShopWise-AI-Intelligent-Shopping-Assistant-LangGraph-Vector-DB-Streamlit-.git
cd agenticAI
```

### **Create Virtual Environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### **Install Dependencies**

For the main project:
```bash
cd project1
pip install -r requirements.txt
```

For learning notebooks:
```bash
pip install jupyter pandas numpy langchain sentence-transformers
```

### **Set Up Environment Variables**
Create `.env` file:
```env
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_key  # Optional
ANTHROPIC_API_KEY=your_anthropic_key  # Optional
```

---

## 📊 Project Comparison

| Feature | example1 | project1 (ShopWise AI) |
|---------|----------|------------------------|
| Agent Type | Basic | LangGraph ReAct |
| Search | Keyword only | Semantic + Visual |
| Database | SQLite | SQLite + Vector DB |
| UI | Basic | Premium Design |
| Auth | None | Full system |
| Deployment | Local only | Cloud-ready |
| Production | ❌ | ✅ |

---

## 🎯 Key Concepts Demonstrated

### **Agent Patterns**
- ✅ Tool calling and function execution
- ✅ ReAct (Reasoning + Acting) pattern
- ✅ Stateful conversation with checkpointing
- ✅ Memory and context management

### **RAG Techniques**
- ✅ Document chunking strategies
- ✅ Embedding generation
- ✅ Semantic similarity search
- ✅ Context retrieval and injection

### **Vector Databases**
- ✅ Embedding storage and retrieval
- ✅ Similarity metrics (cosine, dot product)
- ✅ Hybrid search (keyword + semantic)
- ✅ Filter combination

### **Production Practices**
- ✅ Error handling and retries
- ✅ Caching for performance
- ✅ Security (auth, password hashing)
- ✅ Database migrations
- ✅ Configuration management
- ✅ Deployment automation

---

## 🐛 Troubleshooting

### **Common Issues**

**Import errors:**
```bash
pip install -r project1/requirements.txt
```

**Database locked:**
```bash
# Delete and reinitialize
rm project1/store.db
python project1/setup_db.py
```

**Model download timeout:**
- First run downloads ~80MB model (takes 30-60s)
- Model is cached for subsequent runs

**API key errors:**
- Check `.env` file exists
- Verify key format (should start with `gsk_` for GROQ)
- No extra spaces or quotes

---

## 📚 Resources

### **Official Documentation**
- [LangChain Docs](https://python.langchain.com/)
- [LangGraph Guide](https://langchain-ai.github.io/langgraph/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [GROQ API](https://console.groq.com/docs)

### **Learning Materials**
- [LangChain Cookbook](https://github.com/langchain-ai/langchain/tree/master/cookbook)
- [RAG Tutorial](https://python.langchain.com/docs/tutorials/rag)
- [Vector Database Guide](https://www.pinecone.io/learn/vector-database/)

### **Community**
- [LangChain Discord](https://discord.gg/langchain)
- [Streamlit Forum](https://discuss.streamlit.io/)

---

## 🤝 Contributing

This is a learning repository. Feel free to:
- Fork and experiment
- Add your own examples
- Improve documentation
- Share learnings

---

## 📄 License

MIT License - See individual project folders for specific licenses.

---

## 👨‍💻 Author

**Repository Maintainer:** annamalai199

**Featured Project:** ShopWise AI - Production-ready intelligent shopping assistant

---

## 🎓 What You'll Learn

By exploring this repository, you'll understand:

1. **How to build production AI agents** with LangGraph
2. **How to implement semantic search** with vector embeddings
3. **How to create multi-modal AI apps** with vision models
4. **How to deploy AI apps** to Streamlit Cloud
5. **How to structure AI projects** for maintainability
6. **How to handle authentication** in AI apps
7. **How to optimize performance** with caching
8. **How to debug and troubleshoot** AI systems

---

## 🚀 Next Steps

1. ✅ Clone the repository
2. ✅ Set up your environment
3. ✅ Run the notebooks in order
4. ✅ Deploy ShopWise AI to Streamlit Cloud
5. ✅ Build your own agentic AI application!

---

## 📞 Support

- **Issues:** Open an issue on GitHub
- **Questions:** Check project1/README.md for detailed docs
- **Deployment:** See project1/DEPLOYMENT.md

---

**Happy Learning! 🎉**

Build intelligent agents. Master RAG. Deploy to production.
