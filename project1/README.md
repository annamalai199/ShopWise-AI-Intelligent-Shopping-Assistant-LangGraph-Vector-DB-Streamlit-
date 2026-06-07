# 🛍️ ShopWise AI - Intelligent Shopping Assistant

A production-grade AI-powered shopping platform featuring semantic search, visual product discovery, personalized recommendations, and natural language ordering.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ✨ Features

### 🤖 AI-Powered Shopping Experience
- **Natural Language Search** - "Show me organic honey under $15 with 4+ stars"
- **Visual Product Search** - Upload an image to find similar products
- **Semantic Understanding** - AI comprehends context and intent
- **Intelligent Recommendations** - Personalized product suggestions

### 🔐 User Management
- **Secure Authentication** - Email/password login with session management
- **User Profiles** - Track search history and order patterns
- **Guest Mode** - Full shopping experience without registration
- **Password Management** - Secure password change functionality

### 🎨 Luxury Editorial UI Design
- **Professional Aesthetic** - Linear.app / Stripe inspired interface
- **Clean White Backgrounds** - High contrast, accessible design
- **Emerald Green Accents** - Single bold accent color throughout
- **Editorial Typography** - Playfair Display + IBM Plex Sans

### 🛒 Shopping Capabilities
- **32+ Premium Products** - Curated organic and specialty items
- **Advanced Filtering** - By price, rating, category, dietary needs
- **Real-time Stock Updates** - Live inventory management
- **Instant Checkout** - One-click ordering with confirmation
- **Order History** - View past purchases and reorder easily

### 🧠 Memory & Personalization
- **Search Pattern Learning** - Remembers your preferences
- **Order History Tracking** - Build personalized recommendations
- **User Statistics** - Track searches and purchases

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)

### Installation

1. **Clone or navigate to the project:**
```bash
cd d:\agenticAI\project1
```

2. **Create virtual environment (recommended):**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here  # Optional
```

5. **Initialize the database:**
```bash
python setup_db.py
```

6. **Run the application:**
```bash
streamlit run app.py
```

7. **Open your browser:**
Navigate to `http://localhost:8501`

---

## 📁 Project Structure

```
project1/
├── app.py                  # Main Streamlit application
├── auth_ui.py              # Authentication interface
├── auth_manager.py         # User authentication logic
├── shopping_agent.py       # AI agent with tool calling
├── memory_manager.py       # User personalization & history
├── vector_search.py        # Semantic search engine
├── reviews_api.py          # Product reviews & ratings
├── config.py               # Feature flags & configuration
├── setup_db.py             # Database initialization
├── requirements.txt        # Python dependencies
├── .gitignore              # Git ignore rules
├── .env                    # Environment variables (create this)
├── store.db                # SQLite database (generated)
├── resources/              # Product images
│   ├── honey.png
│   ├── oats.png
│   └── elephant.png
└── __pycache__/            # Python cache (ignored)
```

---

## 🎯 Key Technologies

### Core Stack
- **Streamlit** - Web application framework
- **LangChain** - AI agent orchestration
- **OpenAI GPT-4** - Language model for AI agent
- **ChromaDB** - Vector database for semantic search
- **SQLite** - Relational database for users, products, orders

### AI & Machine Learning
- **Sentence Transformers** - Text embeddings for semantic search
- **CLIP** - Vision-language model for image search
- **Tool Calling** - Function calling with structured outputs

### Authentication & Security
- **bcrypt** - Password hashing
- **Session Management** - Token-based authentication
- **Remember Me** - 30-day persistent sessions

---

## 🛠️ Configuration

### Feature Flags (`config.py`)
```python
ENABLE_AUTH = True      # User authentication system
ENABLE_MEMORY = True    # Personalization & history
```

### Environment Variables (`.env`)
```env
OPENAI_API_KEY=sk-...           # Required: OpenAI API key
ANTHROPIC_API_KEY=sk-ant-...    # Optional: Anthropic API key
```

---

## 📊 Database Schema

### Tables
1. **products** - Product catalog (id, name, category, price, stock, etc.)
2. **product_embeddings** - Vector embeddings for semantic search
3. **reviews** - Product ratings and review text
4. **users** - User accounts and credentials
5. **sessions** - Active user sessions for authentication
6. **orders** - Order history with user associations
7. **user_profiles** - User metadata (display_name, created_at, last_seen)
8. **search_history** - Search queries for personalization
9. **login_attempts** - Failed login tracking for security

---

## 🎨 UI Design System

### Color Palette
```css
Background:  #ffffff (white)
Surface:     #f8f9fa (light gray)
Text:        #111827 (charcoal)
Accent:      #059669 (emerald green)
Border:      #e5e7eb (light gray)
```

### Typography
- **Headings:** Playfair Display (serif)
- **UI/Body:** IBM Plex Sans (sans-serif)

### Component Library
- Clean white cards with subtle shadows
- Emerald green primary buttons
- 1px gray borders throughout
- Smooth 150ms transitions

---

## 🤖 AI Agent Tools

The shopping agent has access to these tools:

1. **search_products** - Semantic product search with filters
2. **get_product_reviews** - Fetch product ratings and reviews
3. **checkout** - Process orders with confirmation
4. **list_all_products** - Show complete product catalog
5. **analyze_product_image** - Visual search from uploaded images

---

## 👤 User Flows

### New User Registration
1. Click "Register" tab on auth page
2. Fill in full name, email, username, password
3. System creates profile automatically
4. Auto-login after successful registration

### Guest Experience
1. Click "Guest" tab or "Continue as Guest" button
2. Full shopping access without registration
3. No saved preferences or order history
4. Upgrade prompt after 6+ interactions

### Authenticated Shopping
1. Login with email and password
2. View personalized welcome message
3. See search/order statistics in sidebar
4. All orders saved to history
5. Profile and password management available

---

## 🔧 Development

### Running Tests
```bash
# No test suite currently - add your tests here
pytest tests/
```

### Database Reset
```bash
# Delete existing database
del store.db

# Reinitialize
python setup_db.py
```

### Adding Products
Edit `setup_db.py` to add more products to the catalog.

---

## 📝 API Usage

### OpenAI API
- **Model:** GPT-4 (gpt-4-0613)
- **Features:** Function calling, streaming responses
- **Rate Limits:** Follow OpenAI's rate limits

### Embeddings
- **Model:** all-MiniLM-L6-v2 (Sentence Transformers)
- **Dimension:** 384
- **Use:** Semantic search and similarity matching

---

## 🐛 Troubleshooting

### Database Errors
```bash
# If you see "table not found" errors:
python setup_db.py
```

### Missing Dependencies
```bash
# Reinstall all requirements:
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use
```bash
# Use a different port:
streamlit run app.py --server.port 8502
```

### API Key Issues
- Verify `.env` file exists in project root
- Check `OPENAI_API_KEY` is set correctly
- Ensure no extra spaces in key

---

## 🚀 Deployment

### Streamlit Cloud
1. Push to GitHub repository
2. Connect to Streamlit Cloud
3. Add secrets in dashboard (API keys)
4. Deploy

### Docker (Future)
```dockerfile
# Dockerfile coming soon
```

---

## 📈 Future Enhancements

- [ ] Product reviews submission by users
- [ ] Advanced filtering (dietary, allergens, brands)
- [ ] Shopping cart for multi-item orders
- [ ] Payment integration (Stripe)
- [ ] Email notifications for orders
- [ ] Admin dashboard for inventory management
- [ ] Product recommendations ML model
- [ ] Multi-language support

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 👨‍💻 Author

ShopWise Engineering Team

---

## 🙏 Acknowledgments

- **OpenAI** - GPT-4 language model
- **LangChain** - Agent framework
- **Streamlit** - Web framework
- **ChromaDB** - Vector database
- **Sentence Transformers** - Embedding models

---

## 📞 Support

For issues or questions:
- Open an issue on GitHub
- Email: support@shopwise.ai (example)

---

**Built with ❤️ using Python, Streamlit, and AI**
