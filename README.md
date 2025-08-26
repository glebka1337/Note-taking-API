# Note-taking API

## Project Description

**Note-taking API** is a complete server application for managing personal notes. Built with **Python** and **FastAPI**, this project is designed for **robustness**, **high performance**, and seamless **CI/CD automation**. It's more than just a simple note-taker; it's a tool for creating a structured knowledge base, similar to a personal wiki.

The core of the application lies in its ability to automatically parse note content and create dynamic, interconnected relationships between ideas.

-----

## Key Features

The API automatically processes your note content to create and manage powerful relationships:

  * **Tags (`#tag`)**: Categorize your notes by simply adding hashtags. The API automatically creates new tags or links to existing ones.
  * **Links (`[Title](uuid)`)**: Create explicit, bidirectional links to other notes. This builds a web of interconnected information, allowing you to easily navigate between related topics.
  * **Nested Notes (`[[ChildNote]]`)**: Organize your thoughts hierarchically by linking to child notes using double brackets.

The system includes a full suite of features:

  * **Full CRUD**: A comprehensive set of endpoints for creating, reading, updating, and deleting notes.
  * **Authorization**: API endpoints are protected using secure authentication.
  * **Automated Testing**: A fully integrated **CI/CD pipeline** with GitHub Actions ensures code quality and reliability with every change.
  * **Containerization**: The entire project is containerized with Docker, making it easy to set up and deploy in any environment.

-----

## Tech Stack

  * **Backend**: FastAPI, Python
  * **Database**: PostgreSQL
  * **ORM**: SQLAlchemy 2.0 (Async)
  * **Caching**: Redis
  * **Testing**: Pytest
  * **Orchestration**: Docker, Docker Compose
  * **CI/CD**: GitHub Actions

-----

## Getting Started

To get the project up and running locally, you only need to have **Docker** and **Docker Compose** installed.

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/glebka1337/Note-taking-API.git
    cd Note-taking-API
    ```

2.  **Configure environment variables**:
    Create a `.env` file in the root directory. You can use the provided `.env.test` file as a reference.

-----

## Project Structure

```text
.
├── api/                  # Main application code
├── tests/                # Pytest tests
├── .github/              # GitHub Actions CI pipeline
├── docker-compose.yml    # Main Docker Compose file
├── docker-compose.dev.yml# Dev-specific Compose file
├── Dockerfile            # Docker image build instructions
├── .env                  # Environment variables
├── .env.test             # Testing environment variables
├── entrypoint.sh         # Container entrypoint script
├── flush-dev.sh          # Script to reset the database
└── README.md
```

-----

## API Documentation

Once the server is running, you can access the interactive API documentation at these URLs:

* **Swagger UI**: `http://localhost:8000/docs`

## Aditional information

* Have any ideas? Create a push request
* Want to build UI? I am opened to your suggestions!
