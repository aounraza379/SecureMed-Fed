# SecureMed-Fed: Privacy-Preserving IoT Healthcare Framework

## Project Overview
SecureMed-Fed is a software-defined IoT ecosystem designed for the secure, real-time monitoring of cardiac health in elderly patients. The system addresses the critical global challenge of **Medical Data Privacy** by ensuring that sensitive vitals never leave the patient's local environment in their raw form.

## Core Features & Technology Stack
- **IoT Simulation:** Real-time synthetic data generation for cardiac monitoring (BPM, SpO2).
- **Edge Intelligence:** Localized anomaly detection algorithms to identify cardiac distress without cloud dependency.
- **Federated Learning (Privacy):** Implementation of Differential Privacy and data masking to anonymize patient updates.
- **Cryptography (Security):** Integration of **Zero-Knowledge Proofs (ZKP)** and SHA-256 hashing to verify emergency alerts while maintaining data confidentiality.
- **Data Visualization:** Interactive health dashboard built with Plotly for real-time clinician oversight.

## The Problem Solved
Traditional remote monitoring systems are vulnerable to data breaches. SecureMed-Fed uses a **"Privacy-by-Design"** approach, allowing healthcare providers to receive verified emergency alerts without ever accessing the patient's raw, unencrypted database.

## Implementation Phases
1. **Data Engineering:** Developed a robust generator for normal and anomalous cardiac patterns.
2. **Detection Logic:** Built a watchdog system for real-time threshold monitoring.
3. **Security Integration:** Applied ZKP protocols to bridge the gap between "Safety" and "Privacy."
4. **HCI Dashboard:** Developed a dark-mode interactive UI for medical response teams.

## Future Roadmap
- Transition from synthetic data to live Mobile/Wearable sensor APIs.
- Deployment of a decentralized database (Supabase) for encrypted alert storage.
- Implementation of Multi-Agent Systems (Agentic AI) for autonomous emergency dispatch.

---
*Developed as a foundational research project for Master of Science (MS) candidacy in Information Technology.*
