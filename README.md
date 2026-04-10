\# 🌐 Multilingual Cyberbullying Detection Chat Application



A real-time intelligent chat application that detects and blocks cyberbullying messages using Machine Learning, Natural Language Processing (NLP), and multilingual translation support.



This system helps prevent harmful communication by analyzing messages before delivery and blocking toxic content instantly in live chat rooms.



\---



\## 🚀 Features



\- Real-time chat room messaging

\- Cyberbullying message detection using Machine Learning

\- Toxic message blocking before delivery

\- English toxicity filtering

\- Partial multilingual support (Tamil, Hindi experimental)

\- Instant warning popup alerts for harmful messages

\- Live deployed frontend and backend using Render



\---



\## 🧠 Machine Learning Model



This project uses:



\- TF-IDF Vectorizer

\- Multi-Layer Perceptron (MLP) Classifier

\- Cyberbullying Kaggle Dataset for training

\- Approximate validation accuracy: 90%



\### Exported Model Files:

\- `models/mlp\_model.pkl`

\- `models/vectorizer.pkl`



\---



\## 🌍 Language Support



Currently Supported:

\- English (Fully Supported)

\- Tamil (Experimental)

\- Hindi (Experimental)



Note:

Tamil and Hindi full sentence toxicity detection may vary depending on translation quality.



\---



\## 🛠️ Tech Stack



\### Frontend:

\- React.js

\- Vite

\- CSS / Tailwind UI



\### Backend:

\- Python

\- Flask / FastAPI

\- WebSockets



\### Machine Learning:

\- Scikit-learn

\- Pandas

\- NumPy



\### Translation:

\- deep-translator

\- GoogleTranslator API



\---



\## 📂 Project Structure



```bash

cyberbullying/

│

├── frontend/

├── models/

│   ├── mlp\_model.pkl

│   └── vectorizer.pkl

│

├── app.py

├── train.py

├── requirements.txt

├── README.md

└── .gitignore



🌐 Live Demo



🔗 Frontend Application:

https://cyberbullying-frontend-9uqz.onrender.com/



🔗 Backend API:

https://cyberbullying-a2nu.onrender.com/

