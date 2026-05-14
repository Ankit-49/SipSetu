import fitz  # PyMuPDF
import docx
import os

def extract_text(file_path: str) -> str:
    """
    Extracts text from a PDF or DOCX file.
    
    Args:
        file_path (str): The absolute path to the file.
        
    Returns:
        str: The extracted text.
        
    Raises:
        ValueError: If the file type is unsupported.
        FileNotFoundError: If the file does not exist.
        Exception: For other parsing errors.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_path.lower().endswith('.pdf'):
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text.strip()
        except Exception as e:
            raise Exception(f"Error parsing PDF: {str(e)}")
            
    elif file_path.lower().endswith('.docx'):
        try:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise Exception(f"Error parsing DOCX: {str(e)}")
            
    else:
        raise ValueError(f"Unsupported file type: {os.path.splitext(file_path)[1]}. Supported types are .pdf and .docx")
