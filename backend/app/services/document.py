import fitz  # PyMuPDF
import re
from typing import List, Dict

class DocumentService:
    def parse_markdown(self, content: str) -> List[Dict]:
        """解析 Markdown，按段落分块"""
        # 按标题分割
        sections = re.split(r'\n(?=#{1,3}\s)', content)
        chunks = []
        
        for section in sections:
            if not section.strip():
                continue
            
            # 提取标题
            title_match = re.match(r'^(#{1,3})\s+(.+)$', section, re.MULTILINE)
            title = title_match.group(2) if title_match else "无标题"
            
            # 按固定大小分块（500-800字）
            text = section.strip()
            if len(text) > 800:
                # 按句子分割
                sentences = re.split(r'(?<=[。！？.!?])\s*', text)
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) <= 800:
                        current_chunk += sentence
                    else:
                        if current_chunk:
                            chunks.append({
                                "text": current_chunk.strip(),
                                "metadata": {"title": title, "type": "markdown"}
                            })
                        current_chunk = sentence
                
                if current_chunk:
                    chunks.append({
                        "text": current_chunk.strip(),
                        "metadata": {"title": title, "type": "markdown"}
                    })
            else:
                chunks.append({
                    "text": text,
                    "metadata": {"title": title, "type": "markdown"}
                })
        
        return chunks
    
    def parse_pdf(self, file_path: str) -> List[Dict]:
        """解析 PDF，按页和段落分块"""
        doc = fitz.open(file_path)
        chunks = []
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            
            # 按段落分割
            paragraphs = re.split(r'\n\s*\n', text)
            current_chunk = ""
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                if len(current_chunk) + len(para) <= 800:
                    current_chunk += para + "\n"
                else:
                    if current_chunk:
                        chunks.append({
                            "text": current_chunk.strip(),
                            "metadata": {
                                "page": page_num + 1,
                                "type": "pdf"
                            }
                        })
                    current_chunk = para + "\n"
            
            if current_chunk:
                chunks.append({
                    "text": current_chunk.strip(),
                    "metadata": {
                        "page": page_num + 1,
                        "type": "pdf"
                    }
                })
        
        doc.close()
        return chunks

document_service = DocumentService()
