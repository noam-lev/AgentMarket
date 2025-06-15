# AgentMarket MVP

---

## 🚀 Project Overview

AgentMarket is a Minimum Viable Product (MVP) for a digital API marketplace. Its primary goal is to enable **service providers** to list their APIs and allow **AI Agents** (and their developers) to discover and utilize these APIs through **semantic search**. This MVP focuses exclusively on digital APIs, without a payment model or an integrated execution engine.

## ✨ Features (MVP)

* **Provider Management:**
    * Secure registration and login for API providers.
    * Ability for providers to add, view, edit, and delete their listed digital APIs.
* **Service Listing & Semantic Search:**
    * Upload APIs with detailed descriptions and OpenAPI/Swagger specifications.
    * Automatic generation of semantic embeddings for API descriptions to power intelligent search.
    * A public API endpoint for AI agents to perform semantic searches for services.
    * Web interface to view detailed API information, including the OpenAPI spec.
* **Basic Usage Tracking:**
    * Endpoint for AI agents to report usage of a discovered service.

## 🛠️ Technology Stack

* **Backend:** FastAPI (Python)
* **Database:** MongoDB
* **Embedding Service:** OpenAI Embeddings API (or similar)
* **Frontend:** React / Next.js (Planned for future, the current MVP focuses on the backend API and a minimal UI)
* **Authentication:** JWT (JSON Web Tokens)
* **Deployment:** Docker

## ➡️ Getting Started

Follow these steps to get your AgentMarket MVP backend up and running locally.

### Prerequisites

* Python 3.9+
* `uv` (Python package installer)
* `docker` and `docker-compose` (recommended for local MongoDB)
* An OpenAI API Key (for embeddings)

### 1. Clone the Repository

```bash
git clone [https://github.com/your-username/agentmarket.git](https://github.com/your-username/agentmarket.git) # Replace with your repo URL
cd agentmarket