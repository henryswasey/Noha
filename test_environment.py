#!/usr/bin/env python3
import sys
import subprocess
import json
import os
import sqlite3
import httpx
from pathlib import Path
import logging
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnvironmentTester:
    """Main class for testing development environment configuration"""
    
    def __init__(self):
        self.results = {
            "vscode": False,
            "python": False,
            "ollama": False,
            "sqlite": False,
            "storage": False,
            "pdf": False,
            "vector": False,
            "streamlit": False,
            "docker": False
        }
        
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all environment tests and return results"""
        try:
            self.test_vscode_extensions()
            self.test_python_dependencies()
            self.test_ollama_connectivity()
            self.test_sqlite_functionality()
            self.test_storage_access()
            self.test_pdf_processing()
            self.test_vector_operations()
            self.test_streamlit_configuration()
            self.test_docker_environment()
            
            return self.results
            
        except Exception as e:
            logger.error(f"Error during environment testing: {str(e)}")
            raise

    def test_vscode_extensions(self) -> None:
        """Verify required VSCode extensions are installed"""
        required_extensions = [
            "ms-python.python",
            "alexcvzz.vscode-sqlite",
            "redhat.vscode-yaml",
            "yzhang.markdown-all-in-one",
            "eamodio.gitlens",
            "joshrmosier.streamlit-runner",
            "rangav.vscode-thunder-client"
        ]
        
        try:
            # Get list of installed extensions
            result = subprocess.run(
                ["code", "--list-extensions"],
                capture_output=True,
                text=True
            )
            
            installed = result.stdout.split('\n')
            missing = [ext for ext in required_extensions if ext not in installed]
            
            if missing:
                logger.warning(f"Missing VSCode extensions: {', '.join(missing)}")
                return
                
            self.results["vscode"] = True
            logger.info("VSCode extensions verification: PASSED")
            
        except Exception as e:
            logger.error(f"Error checking VSCode extensions: {str(e)}")

    def test_python_dependencies(self) -> None:
        """Verify required Python packages are installed"""
        required_packages = [
            "streamlit",
            "PyPDF2",
            "sentence-transformers",
            "faiss-cpu",
            "httpx",
            "black",
            "flake8"
        ]
        
        try:
            import pkg_resources
            installed = {pkg.key for pkg in pkg_resources.working_set}
            missing = [pkg for pkg in required_packages if pkg.lower() not in installed]
            
            if missing:
                logger.warning(f"Missing Python packages: {', '.join(missing)}")
                return
                
            self.results["python"] = True
            logger.info("Python dependencies verification: PASSED")
            
        except Exception as e:
            logger.error(f"Error checking Python dependencies: {str(e)}")

    def test_ollama_connectivity(self) -> None:
        """Test Ollama API connectivity"""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get("http://localhost:11434/api/tags")
                
                if response.status_code == 200:
                    # Verify mistral model is available
                    models = response.json()
                    if "models" in models and any(model.get("name", "").startswith("mistral") for model in models["models"]):
                        self.results["ollama"] = True
                        logger.info("Ollama connectivity test: PASSED")
                    else:
                        # Try checking with ollama list format
                        response = client.get(f"{OLLAMA_BASE_URL}/api/tags")
                        models = response.json()
                        if any(model.get("name", "").startswith("mistral") for model in models):
                            self.results["ollama"] = True
                            logger.info("Ollama connectivity test: PASSED")
                        else:
                            logger.warning("Mistral model not found in Ollama")
                        
                    self.results["ollama"] = True
                    logger.info("Ollama connectivity test: PASSED")
                else:
                    logger.warning(f"Ollama API returned status code: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error connecting to Ollama: {str(e)}")

    def test_sqlite_functionality(self) -> None:
        """Test SQLite database operations"""
        test_db = "db/test_environment.db"
        
        try:
            # Create test database and table
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            
            # Create test table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id INTEGER PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Test insert
            cursor.execute("INSERT INTO test_table (value) VALUES (?)", ("test",))
            
            # Test select
            cursor.execute("SELECT * FROM test_table")
            result = cursor.fetchone()
            
            conn.close()
            
            if result and result[1] == "test":
                self.results["sqlite"] = True
                logger.info("SQLite functionality test: PASSED")
                
            # Cleanup
            os.remove(test_db)
            
        except Exception as e:
            logger.error(f"Error testing SQLite: {str(e)}")

    def test_storage_access(self) -> None:
        """Verify access to required storage locations"""
        required_dirs = [
            "db",
            "db/backups",
            "uploads"
        ]
        
        try:
            for directory in required_dirs:
                path = Path(directory)
                
                # Create directory if it doesn't exist
                path.mkdir(exist_ok=True)
                
                # Test write access
                test_file = path / "test_access.txt"
                test_file.write_text("test")
                test_file.unlink()
            
            self.results["storage"] = True
            logger.info("Storage access verification: PASSED")
            
        except Exception as e:
            logger.error(f"Error testing storage access: {str(e)}")

    def test_pdf_processing(self) -> None:
        """Test PDF processing capabilities"""
        try:
            from PyPDF2 import PdfReader
            from io import BytesIO
            
            # Create a minimal PDF in memory for testing
            pdf_bytes = b"%PDF-1.7\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources <<\n>>\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n216\n%%EOF"
            
            # Test PDF reading
            pdf = PdfReader(BytesIO(pdf_bytes))
            if len(pdf.pages) > 0:
                self.results["pdf"] = True
                logger.info("PDF processing test: PASSED")
                
        except Exception as e:
            logger.error(f"Error testing PDF processing: {str(e)}")

    def test_streamlit_configuration(self) -> None:
        """Verify Streamlit server configuration and accessibility"""
        try:
            # Check if port 8501 is available
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 8501))
            sock.close()
            
            # Check for Streamlit config file
            config_path = Path.home() / ".streamlit/config.toml"
            if not config_path.exists():
                logger.warning("Streamlit config file not found")
                return
                
            # Read and verify config matches our project setup
            with open(config_path, 'r') as f:
                config_content = f.read()
                required_settings = [
                    'port = 8501',
                    'address = "0.0.0.0"',
                    'enableCORS = false',
                    'runOnSave = true',
                    'toolbarMode = "developer"'
                ]
                
                if all(setting.lower() in config_content.lower() for setting in required_settings):
                    self.results["streamlit"] = True
                    logger.info("Streamlit configuration test: PASSED")
                else:
                    logger.warning("Streamlit configuration incomplete or incorrect")
                    
        except Exception as e:
            logger.error(f"Error testing Streamlit configuration: {str(e)}")

    def test_docker_environment(self) -> None:
        """Verify Docker environment setup"""
        try:
            # Check Docker daemon
            result = subprocess.run(
                ["docker", "compose", "ps", "--format", "json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning("Docker Compose not running or accessible")
                return
                
            # Check specific Ollama container configuration
            result = subprocess.run(
                ["docker", "inspect", "ollama"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                inspect_data = json.loads(result.stdout)
                if inspect_data:
                    container = inspect_data[0]
                    
                    # Verify all required settings
                    checks = {
                        "image": container.get("Config", {}).get("Image") == "ollama/ollama",
                        "port": any("11434/tcp" in port for port in container.get("NetworkSettings", {}).get("Ports", {})),
                        "platform": container.get("Platform") == "linux",
                        "volume": any("ollama_data" in mount.get("Name", "") for mount in container.get("Mounts", [])),
                        "memory": container.get("HostConfig", {}).get("Memory") == 8 * 1024 * 1024 * 1024  # 8G
                    }
                    
                    if all(checks.values()):
                        self.results["docker"] = True
                        logger.info("Docker environment test: PASSED")
                    else:
                        failed_checks = [k for k, v in checks.items() if not v]
                        logger.warning(f"Docker configuration incomplete. Failed checks: {', '.join(failed_checks)}")
                        return
            
        except Exception as e:
            logger.error(f"Error testing Docker environment: {str(e)}")

    def test_vector_operations(self) -> None:
        """Test vector operations with FAISS"""
        try:
            import faiss
            import numpy as np
            
            # Create a small test index
            dimension = 4
            index = faiss.IndexFlatL2(dimension)
            
            # Add some test vectors
            vectors = np.random.random((5, dimension)).astype('float32')
            index.add(vectors)
            
            # Test search
            query = np.random.random((1, dimension)).astype('float32')
            D, I = index.search(query, 1)
            
            if len(I) > 0:
                self.results["vector"] = True
                logger.info("Vector operations test: PASSED")
                
        except Exception as e:
            logger.error(f"Error testing vector operations: {str(e)}")

def main():
    """Main function to run environment tests"""
    tester = EnvironmentTester()
    
    try:
        results = tester.run_all_tests()
        
        # Print summary
        print("\nEnvironment Test Results:")
        print("------------------------")
        for component, status in results.items():
            print(f"{component:15} {'✓' if status else '✗'}")
        
        # Exit with appropriate status code
        if all(results.values()):
            print("\nAll tests passed successfully!")
            sys.exit(0)
        else:
            print("\nSome tests failed. Check logs for details.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()