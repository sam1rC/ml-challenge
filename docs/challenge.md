# **Software Engineer (ML & LLMs) Challenge \- Solution Documentation**

## **Overview**

This document details the end-to-end operationalization of the Flight Delay Prediction model. The solution encompasses model refactoring, API development, cloud infrastructure provisioning via Terraform, and a fully automated CI/CD pipeline using GitHub Actions.

## **Part I: Model Operationalization (model.py)**

### **1.1 Model Selection**

After analyzing the Data Scientist's work in exploration.ipynb, two models stood out for having the best performance (Recall \~0.69 for the minority class "1"):

1. **XGBoost** (with scale_pos_weight)
2. **Logistic Regression** (with class_weight='balanced')

**Decision:** I selected **Logistic Regression**.

- **Rationale:** Since both models yielded identical recall for delays, Logistic Regression was chosen for its engineering advantages:
  - **Lighter Artifact:** The serialized model is significantly smaller than an XGB tree.
  - **Faster Inference:** Simple dot product calculation vs. tree traversal.
  - **Simpler Dependencies:** Removes the need for xgboost and libomp (system dependency issues on macOS/Alpine), simplifying the Docker build.

### **1.2 Feature Engineering & Preprocessing**

To ensure the model works robustly in production (where data arrives one row at a time), the DelayModel class was implemented with strict safeguards:

- **Top 10 Features:** The model is trained _only_ on the 10 most important features identified in the analysis (e.g., OPERA_Latin American Wings, MES_7, TIPOVUELO_I).
- **Consistent Schema:** The preprocess method enforces the existence and order of these 10 columns, filling missing ones with 0\. This prevents shape mismatch errors during inference when specific categories (like a specific airline) are missing from the input payload.

### **1.3 Model Persistence**

- Implemented **joblib** for model serialization instead of pickle for better efficiency with NumPy arrays.
- The class creates/loads a model.joblib artifact automatically, allowing the API to start up instantly without retraining.

## **Part II: API Development (api.py)**

### **2.1 Architecture**

The API was built using **FastAPI** to provide high-performance, asynchronous inference.

- **Global Initialization:** The DelayModel is instantiated at the module level to load the model artifact into memory once during startup (Cold Start optimization).

### **2.2 Validation & Error Handling**

The provided test suite (tests/api/test_api.py) imposed strict requirements that differed from FastAPI's defaults.

- **Schema:** Implemented Pydantic models (Flight, FlightList) to handle batch predictions.
- **Custom Validators:** Added logic to validate MES (1-12) and TIPOVUELO (N/I).
- **Status Code Mapping:** Implemented a custom exception_handler for RequestValidationError. This intercepts FastAPI's default 422 Unprocessable Entity and converts it to 400 Bad Request to satisfy the specific assertions in the test suite.

### **2.3 Dependency Resolution**

Several "Dependency Hell" issues were resolved to make the legacy test environment work with modern Python:

- Pinned anyio\<4.0.0 to fix AttributeError: start_blocking_portal in FastAPI.
- Pinned pydantic\<2.0.0 to maintain compatibility with the existing codebase structure.

## **Part III: Infrastructure & Deployment**

### **3.1 Containerization (Docker)**

- **Base Image:** python:3.10-slim for a secure, lightweight footprint.
- **Architecture:** Implemented cross-platform builds (--platform linux/amd64) to ensure the image built on local Apple Silicon machines works correctly on Google Cloud's x86 servers.
- **Optimization:** Requirements are copied and installed _before_ the application code to leverage Docker layer caching.

### **3.2 Infrastructure as Code (Terraform)**

The infrastructure is fully managed via Terraform modules, located in challenge/terraform/.

- **Modules:**
  - artifact_registry: Provisions the private Docker repository.
  - cloud_run: Provisions the serverless service with public access (allUsers).
- **Production Configuration:**
  - **Auto-Enable APIs:** The configuration automatically enables run.googleapis.com and artifactregistry.googleapis.com.
  - **Resource Tuning:** Memory was increased to **2Gi** to handle the overhead of loading Pandas and Scikit-Learn, preventing crashes during initialization.
  - **Startup Probe:** Configured a TCP startup probe to give the container sufficient time to load the model before health checks begin, effectively solving "Cold Start" timeouts.

### **3.3 Stress Testing**

- Executed make stress-test using **Locust**.
- **Result:** The API successfully handled **100 concurrent users** with a **0% failure rate** and an average latency of \~320ms.
- **Fix:** Pinned jinja2 and itsdangerous versions in requirements-test.txt to resolve compatibility issues with Locust.

## **Part IV: CI/CD Automation**

### **4.1 Continuous Integration (ci.yml)**

- **Trigger:** Runs on every push and pull_request to main or develop.
- **Pipeline:**
  1. Sets up Python 3.10 with pip caching.
  2. Installs production and testing dependencies.
  3. Runs make model-test to validate model logic.
  4. Runs make api-test to validate API contracts.

### **4.2 Continuous Delivery (cd.yml)**

- **Trigger:** Runs strictly on pushes to the main branch.
- **Security:** Authenticates to Google Cloud using **Workload Identity Federation** (or Service Account Key via Secrets) without hardcoding credentials.
- **Pipeline:**
  1. Builds the Docker image (linux/amd64).
  2. Pushes the image to the **Artifact Registry** created by Terraform.
  3. Deploys the new revision to **Cloud Run** using the google-github-actions/deploy-cloudrun action.

### **4.3 Secrets Management**

- **GCP_CREDENTIALS**: Service Account JSON key stored as a GitHub Secret within the production environment scope, ensuring secure deployment access.
