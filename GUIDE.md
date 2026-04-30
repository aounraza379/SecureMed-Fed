# SecureMed-Fed

A secure federated learning system for elderly monitoring using IoT devices.

## Project Structure

- `core/privacy.py`: Federated Learning and data masking logic
- `core/security.py`: Zero-Knowledge Proof (ZKP) implementation
- `data/patient_data.csv`: Synthetic patient data for training
- `app.py`: Flask application for IoT data ingestion
- `dashboard.py`: Streamlit dashboard for real-time visualization

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the Flask app:
   ```bash
   python app.py
   ```

3. Run the dashboard:
   ```bash
   streamlit run dashboard.py
   ```

## Phases

1. Data Generation: Synthetic patient data creation
2. Monitoring: Basic threshold-based alerts
3. Privacy: Federated learning with differential privacy
4. Security: ZKP for emergency verification
5. Visualization: Real-time dashboard