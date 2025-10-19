"""PDF processing utilities for extracting text and table of contents."""

import io
import re
from typing import List, Dict, Any
import PyPDF2
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class PDFProcessor:
    """Handles PDF file processing and text extraction."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Extract text content from PDF bytes."""
        try:
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            print(f"\n📖 DEBUG: PDF has {len(pdf_reader.pages)} pages")
            
            text = ""
            for i, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                text += page_text + "\n"
                print(f"📄 DEBUG: Page {i} - extracted {len(page_text)} characters")
                if i <= 2:  # Show preview of first 2 pages
                    print(f"   Preview: {page_text[:150].strip()}...")
            
            print(f"\n📋 DEBUG: Total extracted text: {len(text)} characters")
            print(f"📋 DEBUG: First 300 characters of extracted text:")
            print("-" * 50)
            print(text[:300] + "..." if len(text) > 300 else text)
            print("-" * 50)
            
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error extracting text from PDF: {str(e)}")
    
    def extract_table_of_contents(self, pdf_content: bytes) -> List[Dict[str, Any]]:
        """Extract table of contents from PDF."""
        try:
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            toc = []
            
            # Try to get bookmarks/outline
            if hasattr(pdf_reader, 'outline') and pdf_reader.outline:
                toc = self._parse_outline(pdf_reader.outline)
            else:
                # Fallback: create basic TOC from page content
                toc = self._create_basic_toc(pdf_reader)
            
            return toc
        except Exception as e:
            raise ValueError(f"Error extracting table of contents: {str(e)}")
    
    def _parse_outline(self, outline, level: int = 0) -> List[Dict[str, Any]]:
        """Parse PDF outline/bookmarks into structured TOC."""
        toc = []
        
        for item in outline:
            if isinstance(item, list):
                toc.extend(self._parse_outline(item, level + 1))
            else:
                try:
                    page_num = item.page.idnum if hasattr(item, 'page') else None
                    toc.append({
                        "title": str(item.title),
                        "level": level,
                        "page": page_num
                    })
                except Exception:
                    continue
        
        return toc
    
    def _create_basic_toc(self, pdf_reader) -> List[Dict[str, Any]]:
        """Create a basic table of contents when no outline exists."""
        
        toc = []
        
        # Only check first 3 pages where TOC is typically located
        max_pages_to_check = min(3, len(pdf_reader.pages))
        
        for i in range(max_pages_to_check):
            page = pdf_reader.pages[i]
            text = page.extract_text()
            lines = text.split('\n')
            
            # Look for table of contents indicators
            toc_found = False
            for line in lines:
                line_lower = line.lower().strip()
                if any(indicator in line_lower for indicator in [
                    'table of contents', 'contents', 'index', 'overview'
                ]):
                    toc_found = True
                    break
            
            if toc_found:
                print(f"\n📋 DEBUG: Found TOC indicators on page {i+1}")
                toc.extend(self._extract_toc_from_page(lines, i + 1))
        
        # If no TOC found in first 3 pages, try to extract from first page only
        if not toc and len(pdf_reader.pages) > 0:
            print(f"\n📋 DEBUG: No TOC indicators found, analyzing first page structure")
            first_page_text = pdf_reader.pages[0].extract_text()
            toc = self._extract_toc_from_page(first_page_text.split('\n'), 1)
        
        # Remove duplicates and filter out poor matches
        seen_titles = set()
        filtered_toc = []
        for item in toc:
            title = item['title'].strip()
            if (title not in seen_titles and 
                len(title) > 3 and 
                len(title) < 150 and
                not self._is_likely_noise(title)):
                seen_titles.add(title)
                filtered_toc.append(item)
        
        print(f"\n📋 DEBUG: Extracted {len(filtered_toc)} TOC items")
        for item in filtered_toc:
            print(f"   - {item['title']} (page {item['page']}, level {item['level']})")
        
        return filtered_toc
    
    def _extract_toc_from_page(self, lines: List[str], page_num: int) -> List[Dict[str, Any]]:
        """Extract TOC items from a page's text lines."""
        
        toc_items = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Pattern 1: Numbered items (1., 2., 1.1, etc.)
            numbered_match = re.match(r'^(\d+(?:\.\d+)*)\s*\.?\s+(.+)', line)
            if numbered_match:
                number_part = numbered_match.group(1)
                title = numbered_match.group(2).strip()
                level = number_part.count('.') if '.' in number_part else 0
                
                toc_items.append({
                    "title": title,
                    "level": level,
                    "page": page_num
                })
                continue
            
            # Pattern 2: Bullet points (•, -, *, etc.)
            bullet_match = re.match(r'^[•\-\*]\s+(.+)', line)
            if bullet_match:
                title = bullet_match.group(1).strip()
                toc_items.append({
                    "title": title,
                    "level": 0,
                    "page": page_num
                })
                continue
            
            # Pattern 3: Lines that look like chapter/section titles
            # (all caps, title case, or specific formatting patterns)
            if self._looks_like_toc_entry(line):
                # Try to extract page number if present
                page_match = re.search(r'\.{3,}\s*(\d+)$|\.{2,}\s*(\d+)$|\s+(\d+)$', line)
                extracted_page = page_num
                title = line
                
                if page_match:
                    # Extract page number and clean title
                    extracted_page = int(page_match.group(1) or page_match.group(2) or page_match.group(3))
                    title = re.sub(r'\.{2,}\s*\d+$|\s+\d+$', '', line).strip()
                
                toc_items.append({
                    "title": title,
                    "level": 0,
                    "page": extracted_page
                })
        
        return toc_items
    
    def _looks_like_toc_entry(self, line: str) -> bool:
        """Determine if a line looks like a table of contents entry."""
        
        line = line.strip()
        
        # Skip very short or very long lines
        if len(line) < 5 or len(line) > 120:
            return False
        
        # Skip lines that are clearly not TOC entries
        if any(noise in line.lower() for noise in [
            'page', 'figure', 'table', 'example', 'for instance', 'let\'s', 'try',
            'www.', 'http', '@', 'copyright', '©', 'isbn'
        ]):
            return False
        
        # Positive indicators for TOC entries
        positive_score = 0
        
        # Title case or all caps (common in TOC)
        if line.istitle() or line.isupper():
            positive_score += 2
        
        # Contains dots leading to page numbers
        if re.search(r'\.{3,}\s*\d+$', line):
            positive_score += 3
        
        # Short, concise line (typical of TOC entries)
        if 10 <= len(line) <= 60:
            positive_score += 1
        
        # Contains chapter/section keywords
        if any(keyword in line.lower() for keyword in [
            'chapter', 'section', 'part', 'introduction', 'conclusion', 
            'overview', 'summary', 'appendix', 'index', 'references'
        ]):
            positive_score += 2
        
        # Starts with common TOC prefixes
        if re.match(r'^(Chapter|Part|Section|Unit|Lesson)\s+\d+', line, re.IGNORECASE):
            positive_score += 3
        
        return positive_score >= 2
    
    def _is_likely_noise(self, text: str) -> bool:
        """Check if text is likely noise and not a real TOC entry."""
        text_lower = text.lower().strip()
        
        # Common noise patterns
        noise_patterns = [
            'for example', 'let\'s try', 'another one', 'problem solving',
            'page', 'figure', 'table', 'equation', 'formula',
            'copyright', 'isbn', 'published', 'edition',
            'www.', 'http', '@', '.com', '.org',
            'and', 'the', 'of', 'to', 'in', 'for', 'with'
        ]
        
        # Check if it's mostly noise
        if any(pattern in text_lower for pattern in noise_patterns):
            return True
        
        # Check if it's too generic or short
        if len(text.strip()) < 4:
            return True
        
        # Check if it's all numbers or symbols
        if re.match(r'^[\d\s\.\-\+\*\/\(\)]+$', text):
            return True
        
        return False
    
    def split_text_into_chunks(self, text: str, metadata: Dict[str, Any] = None) -> List[Document]:
        """Split text into chunks for vector storage."""
        if metadata is None:
            metadata = {}
        
        chunks = self.text_splitter.split_text(text)
        print(f"\n🧩 DEBUG: Split text into {len(chunks)} chunks")
        print(f"🧩 DEBUG: Chunk size: {self.chunk_size}, Overlap: {self.chunk_overlap}")
        
        documents = []
        
        for i, chunk in enumerate(chunks):
            doc_metadata = {
                **metadata,
                "chunk_id": i,
                "total_chunks": len(chunks)
            }
            documents.append(Document(page_content=chunk, metadata=doc_metadata))
            
            # Show preview of first few chunks
            if i < 3:
                print(f"\n--- CHUNK {i+1} ---")
                print(f"Length: {len(chunk)} characters")
                print(f"Content: {chunk[:200]}...")
        
        print(f"\n✅ DEBUG: Created {len(documents)} document objects for vector storage")
        return documents 