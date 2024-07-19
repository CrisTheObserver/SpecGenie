# SpecGenie

This project's goal is to provide an easy way to generate spec sheets of products from the e-commerce using Large Language Models (LLMs) such as Gemini and ChatGPT.

## How the App Works

1. Users access the API to interact with LLMs for testing responses, retrieving categories and prompts, and obtaining sheets for specific products.
2. The API handles user requests by utilizing endpoints implemented in Django.
3. Utility functions and classes process data and interact with LLM APIs (Gemini and ChatGPT) to generate responses.
4. Users can perform various tasks such as testing LLM responses, retrieving categories and prompts, and obtaining sheets based on product queries.
5. An additional feature allows using Google search to gather context for product queries.

## How to Develop

### Project Structure

The project follows a Django-based structure with the following components:
- **api.py**: Defines API endpoints for interacting with LLMs.
- **scripts.py**: Contains utility functions and classes for LLM interaction, including Google search integration.
- **specgenie/models.py**: Defines database models for categories, prompts, and ground truth products.
- **enums.py**: Defines Enum classes for representing available LLMs, roles, and languages.
- **admin.py**: Configures the Django admin interface for managing categories, prompts, ground truth products, and attributes.

### Running the Application

To set up the development environment:
1. Clone the repository.
2. Install the required dependencies listed in `requirements.txt`.
3. Configure the Django project settings.
4. Run migrations to create the database schema.
5. (Optional) Populate the database with default products for the Ground Truth and Prompts using `loaddata`:
   ```bash
   python manage.py loaddata data.json
   ```
6. Start the Django development server.

### Adding and Using Prompts

To add custom prompts and use them in the application:

1. Access the Django admin interface by navigating to `/admin` on the development server.
2. Log in with appropriate credentials.
3. Navigate to the "Prompts" section.
4. Click on "Add Prompt" to create a new prompt.
5. Enter the category, number, version, and content for the prompt.
6. Select the corresponding language and role for the prompt (if needed you can create a new one).
7. Save the prompt.
8. In your code, you can use the `get_prompt` function from `scripts.py` to retrieve the custom prompt based on the provided category, number, and version.
9. Use the retrieved prompt in your application logic as needed.

## How the Code Works
Files on the `backend` folder:
- **api.py**: Implements API endpoints using the Ninja framework. It handles requests for testing LLM responses, retrieving categories and prompts, and obtaining spec sheets. Now includes Google search integration to gather context for product queries.
- **scripts.py**: Provides utility functions for processing JSON data, interacting with LLM APIs (Gemini and ChatGPT), evaluating LLM responses, and performing Google searches to gather additional context for product queries.
- **enums.py**: Defines Enum classes `LLMEnum`, `RoleEnum`, and `LangEnum` for representing roles and languages for prompts, along with available LLMs.

Files on the `specgenie` folder:
- **models.py**: Defines Django models for categories, prompts, ground truth attributes, ground truth products, and product attributes.
- **admin.py**: Configures the Django admin interface for managing categories, prompts, ground truth products, and attributes.

## TO DO

- Improve error handling in API endpoints.
- Enhance documentation for utility functions and classes.
- Implement additional features, such as user authentication and authorization.
- Enhance testing coverage for API endpoints and utility functions.