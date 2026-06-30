# Bidirectional Trust-Based Framework for IoST with Secured Recommendation Sharing

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Django](https://img.shields.io/badge/Django-4.0%2B-092E20.svg?logo=django)](https://www.djangoproject.com/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.0%2B-FF6F00.svg?logo=tensorflow)](https://www.tensorflow.org/)

This project simulates a highly robust, dual-backend Trust Management Protocol. It evaluates multiple dimensions like User, Device, and Service in real-time to detect and mitigate malicious activities in a network.

## 🚀 Key Features

* **Multi-Dimensional Trust Calculation**: Calculates dynamic trust scores based on real-time interactions across multiple dimensions.
* **Dual-Backend Architecture**: Utilizes **FastAPI** for high-performance, real-time trust calculations and transaction logging, alongside **Django** for administrative services and overall system orchestration.
* **Adversarial Threat Modeling**: Simulates a network of multiple nodes and 15,000+ interactions, accurately modeling complex network attacks including attacks like:
  * Bad-Mouthing / Ballot-Stuffing
  * Discriminatory Attacks
  * On-Off Attacks
  * Opportunistic Service Attacks
* **Machine Learning Threat Detection**: Features a Deep Learning multi-label classification pipeline built with **TensorFlow** and **Scikit-Learn** that identifies and mitigates trust attacks, achieving a 0.9526 F-Measure.

## 🛠️ Tech Stack

* **Backend Frameworks**: FastAPI, Django, Django REST Framework
* **Machine Learning**: TensorFlow (Keras), Scikit-Learn, Pandas, NumPy
* **Database**: PostgreSQL (via SQLAlchemy and asyncpg)
* **Visualization**: Matplotlib, Seaborn

## 📂 Project Structure

```text
.
├── fastapi_trust_service/      # Core FastAPI microservice for real-time trust calculations
├── django_admin_service/       # Django backend for admin orchestration and user management
├── simulator.py                # Generates the simulated IoST environment and node interactions
├── attack_module.py            # TensorFlow Deep Learning model for attack detection
├── graphs.py                   # Data visualization scripts for system performance metrics
├── requirements.txt            # Project dependencies
└── interactions_log.csv        # Output dataset of network interactions (generated post-simulation)
```

## ⚙️ Setup and Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/PratyakshT/Trust-Based-Management-Protocol.git
   cd Trust-Based-Management-Protocol
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Configuration:**
   Ensure you have PostgreSQL installed and running. Configure your database connection strings inside both `fastapi_trust_service/database.py` and the Django `settings.py`.

## 🏃‍♂️ Usage

**1. Start the microservices**
You will need two separate terminal windows to run both backends concurrently.

*Terminal 1 (FastAPI):*
```bash
cd fastapi_trust_service
uvicorn main:app --reload --port 8001
```

*Terminal 2 (Django):*
```bash
cd django_admin_service
python manage.py runserver 8000
```

**2. Run the Simulation**
Once the services are active, initiate the network interaction simulation. This script registers users/devices and simulates 15,000 interactions to calculate trust and generate the dataset (`interactions_log.csv`).
```bash
python simulator.py
```

**3. Train the Threat Detection Model**
Run the deep learning module to train the multi-label classification model on the newly generated interaction logs.
```bash
python attack_module.py
```
*This will output the Precision, Recall, and F1-Scores and save the trained model as `attack_detection_model.keras`.*

## 📊 Evaluation & Results

By implementing our event-driven bidirectional trust framework, the model successfully identifies malicious network patterns with high precision. 

* **F-Measure**: 0.9526
* **Recall Rate**: 0.9483