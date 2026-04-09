import pandas as pd
import numpy as np
import pickle
import os
import re
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report, accuracy_score

# Clean text function
def clean_text(text):
    text = text.lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\@\w+|\#', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text

def main():
    print("Downloading/Loading dataset...")
    try:
        url = "https://raw.githubusercontent.com/t-davidson/hate-speech-and-offensive-language/master/data/labeled_data.csv"
        df = pd.read_csv(url)
        df.rename(columns={'tweet': 'tweet_text'}, inplace=True)
        # 0: hate speech, 1: offensive language, 2: neither
        # Let's group hate/offensive (0,1) as 1 (cyberbullying) and 2 as 0 (not cyberbullying)
        df['cyberbullying_type'] = df['class'].apply(lambda c: 0 if c == 2 else 1)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return
    print(f"Dataset shape: {df.shape}")
    
    # Check columns
    text_col = 'tweet_text'
    label_col = 'cyberbullying_type'

    print("Cleaning text...")
    df['cleaned_text'] = df[text_col].apply(lambda x: clean_text(str(x)))

    X = df['cleaned_text']
    y = df[label_col].values

    print("Vectorizing Text...")
    # Using TF-IDF to convert text to numerical features
    vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
    X_vec = vectorizer.fit_transform(X)

    print("Splitting dataset...")
    X_train, X_test, y_train, y_test = train_test_split(X_vec, y, test_size=0.2, random_state=42)

    print("Training Multi-Layer Perceptron (MLP) Neural Network...")
    mlp = MLPClassifier(hidden_layer_sizes=(100,), max_iter=20, early_stopping=False, verbose=True, random_state=42)
    mlp.fit(X_train, y_train)

    print("\nEvaluating Model...")
    y_pred = mlp.predict(X_test)
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred))

    print("Saving Model and Vectorizer...")
    os.makedirs('models', exist_ok=True)
    with open('models/mlp_model.pkl', 'wb') as f:
        pickle.dump(mlp, f)
    with open('models/vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)
    print("Training completed. Model saved to 'models/' directory.")

if __name__ == "__main__":
    main()
