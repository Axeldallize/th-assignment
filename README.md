# AI Data Analyst for Pagila Database

This project provides a smart, conversational API that allows users to ask analytical questions about a PostgreSQL database (using the Pagila sample dataset) in plain English and receive accurate answers. I built this system to handle a range of queries, from simple data retrieval to complex, open-ended analytical questions.

---

## Submission Questions

### 1. Briefly describe your process for completing the project from start to finish. Include details on assumptions made and key decisions taken / tradeoffs made for each step (if relevant).

My process was structured around three phases: architectural design, iterative development, and refinement.

First, I focused on selecting the right AI architecture. I considered several options, from a simple Text-to-SQL chain to a complex, multi-tool AI agent. Given the 4-hour time limit, I made the key assumption that a full agent was too risky to debug. I decided on a Tool-Augmented LLM architecture, which offered a modern, powerful balance between the simplicity of a single LLM call and the robustness of an agent that can self-correct using tools.

Next, during development, I built the system piece by piece, starting with the database connection and FastAPI server. I encountered and solved several technical hurdles, from initial Docker environment issues to discovering the database was not being populated correctly. The key decision here was to be systematic: I used the API's `/docs` page to isolate bugs, implemented a regex to reliably extract SQL from the LLM's output, and used `docker-compose down -v` to ensure a clean database state for testing.

Finally, in the refinement phase, I tested the four sample questions. For Question #4 (most/least paid customer), the LLM struggled with the partitioned `payment` table. As a pragmatic tradeoff due to time constraints, I chose to patch the system prompt with a specific instruction to query only the main table. This delivered a correct, concise answer immediately, while I documented the more robust (but time-intensive) "Planner/Resolver" agent as the ideal future solution in the `README.md`.

### 2. Are you happy with your solution? Why or why not?

Short answer - yes, I'm very happy with the solution.

Of course, it successfully fulfills all project requirements: it correctly answers the full range of questions, from simple data retrieval to complex, nuanced analysis. This validates the core architectural decision to use a Tool-Augmented LLM that can handle a stateful, self-correcting conversation.

However, I'm also aware of its limitations as a prototype. While it's effective, its reliance on prompt-engineering for complex cases (like the partitioned table) is not as robust as a more advanced agent. The ideal solution, which I outlined in the `README.md`, would be a "Planner/Resolver" agent that could discover and handle such schema complexities on its own. So, while I'm proud of what I built in the time allotted, I have a clear vision for how to make it production-grade.

### 3. What would you do differently if you got to do this over again?

Given the strict time limit, I believe my risk-managed approach was the right call. It ensured I delivered a working solution on time.

However, in hindsight, knowing I completed the project with a bit of time to spare, I would have been more aggressive in my initial approach. I would have dedicated the first hour to scaffolding a more advanced Planner/Resolver agent architecture directly. While this would have been a riskier start, it might have handled edge cases like the partitioned `payment` table more fundamentally. This would have potentially resulted in a more robust and scalable solution out of the box, capable of answering an even wider range of unforeseen, complex questions.

### 4. Did you get stuck anywhere? How'd you get unstuck?

Yes, I encountered a few challenges, which I broke down into two types: technical hurdles and strategic decisions.

*   Technical Hurdle: Database initialization. My most significant blocker was correctly populating the Docker database. I initially struggled with what I thought were read-only user issues. I got unstuck by systematically debugging: verifying the container logs, confirming the `init-db` scripts were being found, and finally realizing the Docker volume wasn't being re-initialized. The solution was to run `docker-compose down -v` to destroy the old volume, which forced a clean startup that correctly ran the setup scripts.

*   LLM Hurdle: Query hallucination. For Question #4, the LLM initially "hallucinated" incorrect queries by trying to handle the `payment` table's partitions. This is a common challenge in LLM development. I got unstuck through iterative prompt engineering—a core part of the "Tool-Augmented LLM" process—where I explicitly instructed the model to query only the parent table.

*   The "Good" Problem: Architecture Selection. The most time-consuming challenge was a "good" one: choosing the core AI architecture at the start. It wasn't a "stuck" state, but a deep, deliberate process of weighing tradeoffs. The time spent here was crucial, as it gave me a clear and confident path forward and was ultimately why the project succeeded.

---

## AI Architecture Selection

Choosing the right AI architecture was the most critical decision for this project. The goal was to select an approach that could answer all sample questions, including the analytical ones, while being realistically achievable within the time constraints. I evaluated several modern options before arriving at the final design.

Here is a summary of the approaches I considered:

| Architecture | Pros | Cons |
| :--- | :--- | :--- |
| **Full AI Agent (e.g., LangChain SQL Agent)** | Very powerful and flexible; can use multiple tools (SQL, Python) to reason through complex, multi-step problems. | High risk for a timed assignment; can be hard to debug if the agent's reasoning goes wrong; often overkill for single-database queries. |
| **RAG on Schema + Pandas** | Excellent for huge databases; retrieves only relevant schema parts. The pandas part allows for complex, local data manipulation. | Adds significant implementation complexity (embedding, vector store, retrieval logic). Less effective for analytical questions requiring data trends over time. |
| **Simple Text-to-SQL Chain** | Simple and fast to implement. | Fails on analytical questions; cannot form opinions or narratives; very brittle and prone to simple syntax errors. |
| **Tool-Augmented LLM (Chosen)** | Balances power and simplicity; highly controllable and debuggable; handles complex queries and analysis in a single conversational flow. | Requires careful prompt engineering to manage the conversational state and define tool use correctly. |

My decision-making process followed this path:

1.  I first recognized that because of the analytical nature of questions like #3 ("*...is the criticism fair?*"), a **Simple Text-to-SQL Chain** would be insufficient. It could fetch data, but not interpret it.

2.  This led me to consider a **Full AI Agent** using a framework like LangChain. While powerful, I assessed this approach as too risky and complex for a 4-hour assignment. Debugging an autonomous agent's "black box" reasoning could consume the entire time budget.

3.  My initial fallback was a two-step **"Query-Then-Analyze"** chain. This was a safe, pragmatic option, but it felt slightly outdated, requiring two separate, stateless LLM calls which can be inefficient.

4.  I therefore landed on the **Tool-Augmented LLM** as the ideal solution. It captures the power of an agent-like workflow within a single, stateful conversation that is far more controllable and efficient. It represents a modern, best-practice approach that balances capability with implementation feasibility, making it perfect for this challenge.

---

## Core Architecture

This project uses a **Tool-Augmented LLM** architecture. Instead of using separate, disconnected AI calls for different tasks, this approach uses a single, stateful conversation with an AI model to orchestrate the entire process.

The core workflow is as follows:

1.  **Understand & Generate SQL:** The user's question and the database schema are given to the AI. Its first task is to generate the correct PostgreSQL query needed to fetch the relevant data.

2.  **Execute & Self-Correct:** The application executes the generated SQL. If the database returns an error (e.g., due to incorrect SQL syntax), the error is fed *back* to the AI in the same conversation. I prompted the AI to fix its own mistake and generate a new query. This "self-correction" loop makes the system highly robust.

3.  **Analyze & Answer:** Once the SQL executes successfully, the resulting data is given back to the AI. Its final task is to analyze this data in the context of the user's original question and formulate a clear, human-readable answer.

This single-conversation approach was chosen because it's efficient, robust, and allows the AI to maintain context throughout the entire process, leading to more coherent and accurate results.

---

## Security

Security is a critical consideration when allowing an AI to interact with a database. I implemented three key layers of defense:

1.  **Read-Only Database User:** The application connects to the PostgreSQL database using a dedicated user with read-only (`SELECT`) permissions. This is the most important security measure, as it fundamentally prevents the AI from performing any destructive operations (like `DROP`, `UPDATE`, or `DELETE`).

2.  **Query Validation:** Before execution, every SQL query generated by the AI is validated to ensure it is a `SELECT` statement and does not contain any other forbidden keywords. This acts as a secondary line of defense.

3.  **Statement Timeout:** A timeout (e.g., 5 seconds) is enforced on every query sent to the database. This prevents long-running or malicious queries (e.g., a Cartesian join that never finishes) from bogging down the system.

---

## Assumptions & Design Choices

To deliver a functional product within the given timeframe, I made several key assumptions and design choices:

*   **Authentication:** I assumed that this project did not require a user authentication system and would be run in a trusted, local environment.
*   **Security Posture:** I acknowledge that the current security system (query string validation) is not foolproof. A production-grade system would require more advanced measures, such as a dedicated safe execution sandbox or more sophisticated static analysis of the generated SQL.
*   **Zero-Shot Prompting:** For maximum flexibility, I chose to use a "zero-shot" prompting strategy, where the AI is expected to understand the task from the system prompt's instructions alone. While this works well, providing a few examples of questions and their correct SQL queries ("few-shot" prompting) could further improve the consistency and reliability of the generated SQL.
*   **Schema Fetching:** The application currently fetches the entire database schema and includes it in the prompt. While simple and effective for a database of this size, this approach is not scalable. For a production environment with hundreds or thousands of tables, I would implement a RAG (Retrieval-Augmented Generation) system to dynamically retrieve only the most relevant table schemas based on the user's question.

---

## Architectural Tradeoffs & Future Work

A key learning occurred at **5:41 PM PST** while debugging Sample Question #4 ("Which customer has paid the most/least?"). I discovered that the AI was providing inconsistent answers because the database schema was more complex than it appeared. The `payment` table is **partitioned**, a common performance optimization that makes simple queries challenging.

This discovery highlighted a tradeoff between a simple, targeted fix and a more robust, holistic architecture.

### The Pragmatic Solution (Implemented)

To ensure a fully functional product within the time constraints, I implemented a pragmatic "prompt patch." I explicitly added a rule to the system prompt that instructs the AI on how to handle the partitioned `payment` table correctly.

### The Holistic Solution (Future Work)

A superior, production-grade solution would be to evolve the system into a **Planner/Resolver Agent**. This architecture treats the AI as a true "reasoning engine" that can explore and understand schema complexities on its own.

Here's how it would work:
1.  **Planning:** Instead of immediately writing the final SQL, the AI would first create a *plan* to solve the user's question. It would identify potential complexities (like partitioned tables) and outline the steps needed to resolve them.
2.  **Tool Use & Resolution:** The AI would then use its tools (like executing discovery queries to count rows) to learn about the schema's behavior.
3.  **Final Answer:** Once it has resolved the complexities, it would confidently generate the correct final query.

This table summarizes the tradeoff:

| Feature | Prompt Patch (Current) | Planner/Resolver Agent (Future) |
| :--- | :--- | :--- |
| **Intelligence** | AI follows a hard-coded rule I give it. | AI discovers the rule for itself through exploration. |
| **Scalability** | Poor. Requires a new rule for every new schema complexity. | Excellent. The same general logic adapts to new databases. |
| **Robustness** | Brittle. Fails on new complexities I haven't written rules for. | Resilient. It has a built-in method for dealing with uncertainty. |
| **Implementation** | Simple prompt change. (Achievable in minutes) | Complex agentic loop. (Requires significant dev time) |

For this project, I made the deliberate tradeoff to implement the pragmatic solution to guarantee delivery, while identifying the Planner/Resolver agent as the clear path forward for future development. The Planner/Resolver would also solve other potential issues, such as the current structure breaking if a query involves too many numbers or complex calculations.

### AI Analyst Behavior: Constrained vs. Contextual

A second design tradeoff was made regarding how the AI presents its final analysis. An unconstrained AI, when asked for the "most" and "least," would often provide the direct answer and then "helpfully" add extra context, such as the second and third-place runners-up.

While potentially insightful, this behavior is less predictable. I made the deliberate choice to constrain the AI's response via prompt engineering, ensuring it only answers the specific question asked.

*   **Contextual AI:** Provides the direct answer plus other information it deems relevant.
*   **Constrained AI (Implemented):** Provides *only* the information explicitly requested. This makes the API's responses precise, predictable, and easier to parse, guaranteeing that the output directly maps to the user's query.

This decision favors reliability and precision over unprompted, creative analysis.

### Analytical Nuance: Decisive vs. Honest AI

The final, most challenging sample question ("*...is the criticism [about film lengths] fair?*") revealed another key design consideration. The AI consistently returned a nuanced answer, such as "partially fair, but not dramatically so," rather than a simple "yes" or "no."

This is a feature, not a bug. It demonstrates the behavior of a sophisticated analytical system:

*   **Intellectual Honesty:** The AI correctly determined that the underlying data was ambiguous and did not support a strong, simple conclusion. Instead of hallucinating a trend to sound more confident, it accurately reported the data's complexity.
*   **Separation of Observation and Interpretation:** The AI first presented the objective facts (the average film lengths per year) and then provided a subjective interpretation based on those facts.
*   **True Analysis:** This behavior fulfills the project's goal of building an *analytical* system. A simple answer would have been a failure of analysis; a nuanced one proves the system can reason about data.

I made the conscious decision to embrace this nuance. Forcing the AI to be more decisive (e.g., via a prompt like "*You must answer only yes or no*") would have resulted in a less truthful and less valuable system. The current implementation prioritizes accuracy and intellectual honesty over artificial certainty, which is crucial for any trustworthy data product. Future work could involve allowing the user to set a "decisiveness level" to tune the AI's response style based on their needs.

---

## How to Run

Follow these steps to get the project running locally.

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Axeldallize/th-assignment.git
    cd th-assignment
    ```

2.  **Set Up Environment Variables:**
    Create a `.env` file from the example and fill in your details.
    ```bash
    cp .env.example .env
    ```
    You will need to add your PostgreSQL read-only user credentials and your LLM API key.

3.  **Prepare the Database Scripts:**
    This project uses the Pagila sample database. The following commands will download the necessary schema and data files into the `init-db` directory. The `docker-compose` setup will automatically run these scripts the first time it creates the database.
    ```bash
    # Create the directory if it doesn't exist
    mkdir -p init-db
    # Download the schema and data files
    curl -o init-db/1-pagila-schema.sql https://raw.githubusercontent.com/devrimgunduz/pagila/master/pagila-schema.sql
    curl -o init-db/2-pagila-data.sql https://raw.githubusercontent.com/devrimgunduz/pagila/master/pagila-data.sql
    ```

4.  **Start the Database:**
    Make sure you have Docker installed and running. This command will start the database server and automatically populate it using the scripts from the previous step.
    ```bash
    docker-compose up -d
    ```
    *(Note: If you need to reset the database, run `docker-compose down -v` to remove the old data volume before running `up -d` again.)*

5.  **Install Dependencies:**
    First, create and activate a virtual environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
    Now, install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

6.  **Run the API Server:**
    With the virtual environment active, run the server:
    ```bash
    uvicorn app:app --reload
    ```
    The server will be available at `http://127.0.0.1:8000`.

### API Usage Examples

You can interact with the API via the `/docs` endpoint or using `curl`.

**Sample Question 1: Simple Retrieval**
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/query' \
  -H 'Content-Type: application/json' \
  -d '{
  "question": "What actors were in Chocolat Harry?"
}'
```

**Sample Question 2: Aggregation & Ranking**
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/query' \
  -H 'Content-Type: application/json' \
  -d '{
  "question": "Display the top 3 actors who have most appeared in films in the Children category"
}'
```

**Sample Question 3: Analytical**
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/query' \
  -H 'Content-Type: application/json' \
  -d '{
  "question": "A common criticism of modern movies is that they are too long. Can you analyze film lengths over time and determine if that criticism is fair"
}'
```

**Sample Question 4: Min/Max**
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/query' \
  -H 'Content-Type: application/json' \
  -d '{
  "question": "Which customer has paid the most for rentals? What about least?"
}'
```

## Sample Questions

### Simple Data Retrieval
```bash
# Q1: What actors were in Chocolat Harry?
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"question": "What actors were in Chocolat Harry?"}'

# Q2: Display the top 3 actors who have most appeared in films in the Children category
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"question": "Display the top 3 actors who have most appeared in films in the Children category"}'

# Q4: Which customer has paid the most for rentals? What about least?
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"question": "Which customer has paid the most for rentals? What about least?"}'
```

### Analytical Questions
```bash
# Q3: Analyze film lengths over time
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"question": "A common criticism of modern movies is that they are too long. Can you analyze film lengths over time and determine if that criticism is fair"}'
```

## API Documentation

### Endpoints

- `GET /` - API information
- `POST /query` - Submit natural language questions
- `GET /health` - Health check

### Request Format

```json
{
  "question": "Your natural language question about the database"
}
```

### Response Format

**Data Retrieval Response:**
```json
{
  "answer_type": "data",
  "content": [
    {"column1": "value1", "column2": "value2"}
  ],
  "sql_query": "SELECT ..."
}
```

**Analytical Response:**
```json
{
  "answer_type": "analysis", 
  "content": "Detailed analysis with insights...",
  "sql_query": "SELECT ..."
}
```

## Database Schema

The system uses the Pagila database (PostgreSQL sample database) with tables including:
- `actor`, `film`, `category` - Core content
- `customer`, `rental`, `payment` - Business transactions  
- `film_actor`, `film_category` - Relationships

## Configuration

### Environment Variables

```env
# Required
ANTHROPIC_API_KEY=your-key-here

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/pagila

# Optional
MODEL_NAME=claude-sonnet-4-20250514
LOG_LEVEL=INFO
PORT=8000
```

## Development

### Project Structure

```
├── app.py              # FastAPI application
├── config.py           # Configuration management  
├── database.py         # Database utilities
├── llm_client.py       # Anthropic API client
├── prompt_templates.py # LLM prompt templates
├── docker-compose.yml  # Database setup
└── requirements.txt    # Dependencies
```

### Testing

```bash
# Run basic tests
python -c "from database import DatabaseManager; db = DatabaseManager(); print('✅ Database connection works')"

# Test LLM integration
python -c "from llm_client import AnthropicClient; client = AnthropicClient(); print('✅ LLM client works')"
```

## From Prototype to Production: A Roadmap

This project was designed to deliver a robust, working solution within a 4-hour timeframe. The current architecture represents a series of deliberate, pragmatic decisions to meet that goal. The following roadmap outlines how this successful prototype can be evolved into a production-grade enterprise application.

1.  **From Full Schema to On-Demand RAG:**
    *   **Current State:** The entire schema is loaded into the prompt, an approach that is simple and effective for a database of Pagila's size.
    *   **Next Step:** Implement a **Retrieval-Augmented Generation (RAG)** system. Table schemas would be embedded into a vector store, allowing the AI to dynamically retrieve only the tables relevant to the user's query. This is the key to scaling to thousands of tables.

2.  **From Self-Correction to Guaranteed Safety:**
    *   **Current State:** The system cleverly uses the database's own error messages to self-correct, which is a highly effective and modern technique.
    *   **Next Step:** Add a dedicated **Abstract Syntax Tree (AST) parsing** layer. This would validate the SQL *before* execution, providing a deterministic guarantee against malformed or unsafe queries, moving from a reactive to a proactive security model.

3.  **From Agentic Behavior to a True Planner/Resolver Agent:**
    *   **Current State:** The AI exhibits agent-like behavior within a single conversation turn.
    *   **Next Step:** Evolve this into a **Planner/Resolver Agent**. This more advanced agent could break down a single complex question ("Which store is most profitable and why?") into a multi-step plan (e.g., 1. Calculate revenue per store; 2. Calculate costs per store; 3. Synthesize findings). This unlocks a much higher level of analytical capability.

4.  **From Direct Answers to Self-Critiqued Analysis:**
    *   **Current State:** The LLM provides its final analysis in a single step after receiving the data.
    *   **Next Step:** Implement a **self-critique loop**. After generating an initial analysis, a second LLM call could be used to challenge the answer, check for biases, and verify that it directly addresses the user's original question. This adds a layer of robustness to the AI's reasoning, ensuring higher quality insights.

5.  **Standard Production Hardening:**
    *   **Caching Layer:** To improve performance and reduce database load, a caching layer could be added to store results for frequently asked questions.
    *   **User Management & Observability:** For a multi-tenant environment, this would include authentication, detailed logging, and tracing to monitor performance and costs.

## Troubleshooting

If you encounter issues, here are some common solutions:

**Database Connection Error:**
```bash
# Check if database is running
docker-compose ps
docker-compose logs postgres
```

**API Key Error:**
```bash
# Verify API key is set
echo $ANTHROPIC_API_KEY
```

**SQL Execution Error:**
- Check generated SQL in response
- Verify table names and relationships
- Review application logs
