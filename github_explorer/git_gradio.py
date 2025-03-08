import gradio as gr
import requests
import os

import nbformat
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from nbconvert import HTMLExporter
# Cargar variables de entorno
load_dotenv()
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Configurar Groq
os.environ["GROQ_API_KEY"] = GROQ_API_KEY
groq_llm = ChatGroq(model="qwen-2.5-32b")

def search_repos_by_topic(topic):
    """Busca repositorios por topic."""
    print(f"[DEBUG] search_repos_by_topic - Searching for topic: {topic}")
    url = f"https://api.github.com/search/repositories?q=topic:{topic}&sort=stars&order=desc&per_page=5"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    response = requests.get(url, headers=headers)
    print(f"[DEBUG] search_repos_by_topic - Response status: {response.status_code}")
    
    if response.status_code == 200:
        items = response.json().get("items", [])
        results = [{"full_name": item["full_name"], 
                   "stars": item["stargazers_count"],
                   "description": item["description"] or "No description",
                   "language": item["language"] or "Not specified"} 
                  for item in items]
        print(f"[DEBUG] search_repos_by_topic - Found {len(results)} repositories")
        return results
    return []

def search_repos_by_username(username):
    """Busca repositorios por nombre de usuario."""
    print(f"[DEBUG] search_repos_by_username - Searching for user: {username}")
    url = f"https://api.github.com/users/{username}/repos?sort=stars&order=desc"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    response = requests.get(url, headers=headers)
    print(f"[DEBUG] search_repos_by_username - Response status: {response.status_code}")
    
    if response.status_code == 200:
        items = response.json()
        results = [{"full_name": item["full_name"], 
                   "stars": item["stargazers_count"],
                   "description": item["description"] or "No description",
                   "language": item["language"] or "Not specified"} 
                  for item in items]
        print(f"[DEBUG] search_repos_by_username - Found {len(results)} repositories")
        return results
    return []

def search_repos_by_name(name):
    """Busca repositorios por nombre."""
    print(f"[DEBUG] search_repos_by_name - Searching for name: {name}")
    url = f"https://api.github.com/search/repositories?q={name}&sort=stars&order=desc&per_page=5"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    response = requests.get(url, headers=headers)
    print(f"[DEBUG] search_repos_by_name - Response status: {response.status_code}")
    
    if response.status_code == 200:
        items = response.json().get("items", [])
        results = [{"full_name": item["full_name"], 
                   "stars": item["stargazers_count"],
                   "description": item["description"] or "No description",
                   "language": item["language"] or "Not specified"} 
                  for item in items]
        print(f"[DEBUG] search_repos_by_name - Found {len(results)} repositories")
        return results
    return []

def get_default_branch(owner, repo):
    """Obtiene la rama por defecto del repositorio."""
    print(f"[DEBUG] get_default_branch - Checking for {owner}/{repo}")
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    response = requests.get(url, headers=headers)
    print(f"[DEBUG] get_default_branch - Response status: {response.status_code}")
    
    if response.status_code == 200:
        branch = response.json().get("default_branch")
        print(f"[DEBUG] get_default_branch - Default branch found: {branch}")
        return branch
    print(f"[DEBUG] get_default_branch - Error response: {response.text}")
    return None

def fetch_repo_structure(owner, repo):
    """Obtiene la estructura del repositorio."""
    print(f"[DEBUG] fetch_repo_structure - Fetching structure for {owner}/{repo}")
    branch = get_default_branch(owner, repo)
    if not branch:
        print("[DEBUG] fetch_repo_structure - Could not get default branch")
        return None
    
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    response = requests.get(url, headers=headers)
    print(f"[DEBUG] fetch_repo_structure - Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"[DEBUG] fetch_repo_structure - Found {len(data.get('tree', []))} items")
        return data
    print(f"[DEBUG] fetch_repo_structure - Error response: {response.text}")
    return None

def fetch_file(file_url):
    """Obtiene el contenido de un archivo."""
    try:
        print(f"[DEBUG] fetch_file - Original URL: {file_url}")
        
        # Si la URL es normal de GitHub, convertirla a raw
        if "github.com" in file_url:
            raw_url = (file_url.replace("github.com", "raw.githubusercontent.com")
                              .replace("/blob/", "/"))
        else:
            # Convertir URL raw a normal y luego a raw de nuevo
            github_url = (file_url.replace("raw.githubusercontent.com", "github.com")
                                .replace("/master/", "/blob/master/"))
            raw_url = (github_url.replace("github.com", "raw.githubusercontent.com")
                              .replace("/blob/", "/"))
        
        print(f"[DEBUG] fetch_file - Raw URL: {raw_url}")
        
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        response = requests.get(raw_url, headers=headers)
        print(f"[DEBUG] fetch_file - Response status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print(f"[DEBUG] fetch_file - Content length: {len(content)}")
            return content
        
        print(f"[DEBUG] fetch_file - Error response: {response.text}")
        return None
    except Exception as e:
        print(f"[DEBUG] fetch_file - Exception: {str(e)}")
        return None

def search_repositories(search_type, query):
    """Función general de búsqueda de repositorios."""
    if not query:
        return []
    
    if search_type == "Topic":
        repos = search_repos_by_topic(query)
    elif search_type == "Username":
        repos = search_repos_by_username(query)
    elif search_type == "Repository Name":
        repos = search_repos_by_name(query)
    elif search_type == "Direct Path" and "/" in query:
        return [query]
    else:
        return []
    
    return [f"{repo['full_name']} (⭐ {repo['stars']}) - {repo['language']}" for repo in repos]

def build_filtered_tree(tree_data, owner, repo, branch):
    """Construye un árbol filtrado solo con archivos .py y .ipynb."""
    print(f"[DEBUG] build_filtered_tree - Building tree for {owner}/{repo}")
    tree = {}
    base_url = f"https://github.com/{owner}/{repo}/blob/{branch}/"
    print(f"[DEBUG] build_filtered_tree - Base URL: {base_url}")
    
    for item in tree_data:
        if item["type"] == "blob" and item["path"].endswith((".py", ".ipynb")):
            path_parts = item["path"].split("/")
            current_level = tree
            for part in path_parts[:-1]:
                current_level = current_level.setdefault(part, {})
            file_url = base_url + item["path"]
            print(f"[DEBUG] build_filtered_tree - Adding file: {item['path']}")
            print(f"[DEBUG] build_filtered_tree - Full URL: {file_url}")
            current_level[path_parts[-1]] = {
                "url": file_url,
                "path": item["path"],
                "type": "notebook" if item["path"].endswith(".ipynb") else "python"
            }
    
    return tree

def tree_to_html(tree, indent=0):
    """Convierte la estructura de árbol a HTML con formato y funcionalidad."""
    html = ""
    indent_px = indent * 20
    
    for key, value in sorted(tree.items()):
        if isinstance(value, dict) and "url" not in value:
            # Es un directorio
            html += f"""
                <div style='margin-left: {indent_px}px; margin-bottom: 5px;'>
                    <span style='font-weight: bold; color: #666;'>📁 {key}</span>
                </div>
                {tree_to_html(value, indent + 1)}
            """
        else:
            # Es un archivo
            icon = "📓" if value["type"] == "notebook" else "🐍"
            html += f"""
                <div style='margin-left: {indent_px}px; margin-bottom: 8px;'>
                    <div style='display: flex; align-items: center; gap: 10px;'>
                        <span>{icon}</span>
                        <a href='{value["url"]}' target='_blank' style='text-decoration: none; color: #0366d6;'>
                            {key}
                        </a>
                        <button onclick='selectAndAnalyze("{value["url"]}")' 
                                style='padding: 4px 12px; border-radius: 4px; border: 1px solid #0366d6; 
                                       background: white; color: #0366d6; cursor: pointer; 
                                       transition: all 0.2s;'
                                onmouseover='this.style.background="#0366d6"; this.style.color="white"'
                                onmouseout='this.style.background="white"; this.style.color="#0366d6"'>
                            Analyze
                        </button>
                    </div>
                    <div style='margin-top: 4px; margin-left: 20px;'>
                        <span style='color: #666; font-size: 0.9em; font-family: monospace;'>
                            Path: {value["url"]}
                        </span>
                    </div>
                </div>
            """
    
    return html

def get_files_structure(repo_full_name):
    """Obtiene y formatea la estructura de archivos del repositorio."""
    try:
        print(f"[DEBUG] get_files_structure - Processing repo: {repo_full_name}")
        owner, repo = repo_full_name.split(" (")[0].split("/")
        branch = get_default_branch(owner, repo)
        if not branch:
            return "Could not fetch repository structure"
        
        repo_data = fetch_repo_structure(owner, repo)
        if not repo_data or "tree" not in repo_data:
            return "No files found"
        
        tree = build_filtered_tree(repo_data["tree"], owner, repo, branch)
        
        # JavaScript para manejar la selección y análisis
        js = """
        <script>
        function selectAndAnalyze(path) {
            console.log('Analyzing path:', path);
            const fileInput = document.querySelector('input[data-testid="Selected File Path"]');
            if (fileInput) {
                fileInput.value = path;
                fileInput.dispatchEvent(new Event('input', { bubbles: true }));
                
                const analyzeButton = document.querySelector('button[data-testid="Analyze File"]');
                if (analyzeButton) {
                    console.log('Clicking analyze button');
                    analyzeButton.click();
                } else {
                    console.log('Analyze button not found');
                }
            } else {
                console.log('File input not found');
            }
        }
        </script>
        """
        
        return js + tree_to_html(tree)
    except Exception as e:
        print(f"[DEBUG] get_files_structure - Error: {str(e)}")
        return f"Error: {str(e)}"

def annotate_code(content, is_notebook=False):
    """Analiza y anota el código usando el LLM."""
    try:
        print(f"[DEBUG] annotate_code - Content type: {type(content)}")
        print(f"[DEBUG] annotate_code - Is notebook: {is_notebook}")
        
        if is_notebook:
            print("[DEBUG] annotate_code - Processing notebook")
            nb = nbformat.reads(content, as_version=4)
            annotated_cells = []
            for cell in nb.cells:
                if cell.cell_type == "code":
                    print(f"[DEBUG] annotate_code - Processing code cell: {cell.source[:100]}...")
                    prompt = f"""Analyze this Python code and provide comments between the python code provided do it from a point of view where learning and understanding is the most important thing.
                     Follow these rules strictly:
                        1. If an explanation is longer than 200 characters, split it into multiple lines
                        2. Each comment line MUST NOT exceed 200 characters
                        3. Use '# Part X:' prefix for split comments (e.g., '# Part 1: First part of explanation')
                        4. Focus on explaining complex logic and important concepts
                        5. Use clear and concise language
                        6. Format multi-line comments like this:
                        # Part 1: First part of the long explanation...
                        # Part 2: Continuation of the explanation...
                        
                        Code to analyze:
                        {cell.source}
                        """
                    response = groq_llm.invoke(prompt)
                    cell.source = response.content
                annotated_cells.append(cell)
            nb.cells = annotated_cells
            return nbformat.writes(nb)
        else:
            print("[DEBUG] annotate_code - Processing Python file")
            print(f"[DEBUG] annotate_code - Content preview: {content[:100]}...")
            prompt = f"""Analyze this Python code and provide concise comments. Follow these rules strictly:
            1. Keep each comment under 100 characters
            2. Use simple, clear language
            3. Focus on the most important aspects only
            4. Add comments only for key lines or blocks
            5. Skip obvious or self-explanatory code
            
            Code to analyze:
            {content}
            """
            response = groq_llm.invoke(prompt)
            return response.content
    except Exception as e:
        print(f"[DEBUG] annotate_code - Error: {str(e)}")
        return f"Error in code annotation: {str(e)}"

def analyze_file(repo_full_name, file_path):
    """Analiza un archivo específico del repositorio."""
    try:
        print(f"[DEBUG] analyze_file - Starting analysis for repo: {repo_full_name}")
        print(f"[DEBUG] analyze_file - File path: {file_path}")
        
        if not file_path:
            print("[DEBUG] analyze_file - No file path provided")
            return "Please select a file to analyze"
        
        # Usar el file_path completo que viene del selected_file
        content = fetch_file(file_path)
        print(f"[DEBUG] analyze_file - Content fetched: {'Yes' if content else 'No'}")
        
        if content:
            is_notebook = file_path.endswith('.ipynb')
            print(f"[DEBUG] analyze_file - Is notebook: {is_notebook}")
            return annotate_code(content, is_notebook=is_notebook)
        
        print("[DEBUG] analyze_file - Could not fetch content")
        return "Error: Could not fetch file content"
    except Exception as e:
        print(f"[DEBUG] analyze_file - Error: {str(e)}")
        return f"Error analyzing file: {str(e)}"

def convert_notebook_to_html(notebook_content):
    """Convierte un Jupyter Notebook a HTML limpio para mostrar en Gradio."""
    try:
        nb = nbformat.reads(notebook_content, as_version=4)
        html_exporter = HTMLExporter()
        
        # Configurar para excluir outputs
        html_exporter.template_name = 'basic'
        html_exporter.exclude_input = False
        html_exporter.exclude_output = True  # Excluir outputs
        
        html_output, _ = html_exporter.from_notebook_node(nb)
        
        styled_html = f"""
        <style>
            .notebook-container {{
                max-width: 100%;
                margin: 20px auto;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            }}
            .input_area {{
                border: 1px solid #e1e4e8;
                border-radius: 6px;
                margin: 10px 0;
                padding: 10px;
                background: #f6f8fa;
            }}
            .input_area pre {{
                margin: 0;
                padding: 10px;
                background: #f8f9fa;
                font-family: monospace;
                white-space: pre-wrap;
            }}
            .cell {{
                margin: 20px 0;
                padding: 10px;
            }}
        </style>
        <div class="notebook-container">
            {html_output}
        </div>
        """
        return styled_html
    except Exception as e:
        print(f"Error detallado en convert_notebook_to_html: {str(e)}")
        return f"<p>Error al convertir el notebook: {str(e)}</p>"

def create_interface():
    """Crea la interfaz de usuario con Gradio."""
    with gr.Blocks(css="""
        .file-structure { 
            background: #f6f8fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 15px;
            margin: 10px 0;
            font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;
            overflow-x: auto;
        }
        .analysis-column {
            margin-top: 20px;
            padding: 15px;
            border-top: 1px solid #e1e4e8;
        }
        .notebook-cell {
            border: 1px solid #e1e4e8;
            margin: 10px 0;
            padding: 10px;
            border-radius: 4px;
        }
    """) as app:
        gr.Markdown("# GitHub Repository Explorer")
        
        with gr.Row():
            search_type = gr.Radio(
                ["Topic", "Username", "Repository Name", "Direct Path"],
                label="Search Method",
                value="Topic"
            )
            query = gr.Textbox(label="Search Query")
            search_btn = gr.Button("Search")
        
        repos_dropdown = gr.Dropdown(
            label="Select Repository",
            choices=[],
            interactive=True
        )
        
        file_structure = gr.HTML(
            label="Repository Structure",
            elem_classes=["file-structure"]
        )
        
        with gr.Column(elem_classes=["analysis-column"]) as analysis_column:
            selected_file = gr.Textbox(
                label="Selected File Path",
                interactive=True,
                elem_id="selected-file-path"
            )
            analyze_btn = gr.Button(
                "Analyze File",
                elem_id="analyze-button"
            )
            
            # Componentes de salida condicionales según el tipo de archivo
            with gr.Group():
                python_output = gr.Code(
                    label="Python Analysis",
                    language="python",
                    interactive=False,
                    lines=30,
                    elem_id="python-analysis"
                )
                notebook_output = gr.HTML(
                    label="Jupyter Notebook Analysis",
                    elem_id="notebook-analysis"
                )
        
        def analyze_and_show(repo, file_path):
            """Analiza el archivo y muestra el resultado en el componente apropiado."""
            try:
                result = analyze_file(repo, file_path)
                is_notebook = file_path.endswith('.ipynb')
                
                if is_notebook:
                    # Convertir el notebook a HTML con celdas
                    html_result = convert_notebook_to_html(result)
                    return None, html_result
                else:
                    return result, None
            except Exception as e:
                print(f"Error en analyze_and_show: {str(e)}")
                return None, f"Error: {str(e)}"
        
        def update_visibility(file_path):
            """Actualiza la visibilidad de los componentes según el tipo de archivo."""
            is_notebook = file_path.endswith('.ipynb')
            return (
                gr.update(visible=not is_notebook),
                gr.update(visible=is_notebook)
            )
        
        # Eventos
        search_btn.click(
            fn=lambda t, q: gr.Dropdown(choices=search_repositories(t, q)),
            inputs=[search_type, query],
            outputs=repos_dropdown
        )
        
        repos_dropdown.change(
            fn=get_files_structure,
            inputs=[repos_dropdown],
            outputs=file_structure
        )
        
        analyze_btn.click(
            fn=analyze_and_show,
            inputs=[repos_dropdown, selected_file],
            outputs=[python_output, notebook_output]
        )
        
        selected_file.change(
            fn=update_visibility,
            inputs=[selected_file],
            outputs=[python_output, notebook_output]
        )
    
    return app

if __name__ == "__main__":
    app = create_interface()
    app.launch()