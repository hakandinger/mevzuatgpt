class KanunParser:
    """Kanun PDF'lerini parse eden ana sınıf"""
    
    def __init__(self):
        # Regex pattern'leri
        self.patterns = {
            'kanun_no': r'Kanun\s+Numarası\s*[:\-]\s*(\d+)',
            'kabul_tarihi': r'Kabul\s+Tarihi\s*[:\-]\s*([\d/\.]+)',
            'resmi_gazete': r'Tarih:\s*([\d/\.]+)\s+Sayı:\s*(\d+)',
            'kisim': r'^(BİRİNCİ|İKİNCİ|ÜÇÜNCÜ|DÖRDÜNCÜ|BEŞİNCİ|ALTINCI|YEDİNCİ|SEKİZİNCİ|DOKUZUNCU|ONUNCU)\s+KISIM\s*$',
            'bolum': r'^(BİRİNCİ|İKİNCİ|ÜÇÜNCÜ|DÖRDÜNCÜ|BEŞİNCİ|ALTINCI|YEDİNCİ|SEKİZİNCİ|DOKUZUNCU|ONUNCU)\s+BÖLÜM\s*$',
            'madde': r'^(EK\s+)?MADDE\s+(\d+[A-Z]?)\s*[-–—]?\s*',
            'bent': r'^\((\d+)\)\s+(.+)',
            'alt_bent': r'^\s*([a-zçğıöşü])\)\s+(.+)'
        }
        
        # Sayı-Türkçe eşleştirme
        self.sayi_turkce = {
            'BİRİNCİ': '1', 'İKİNCİ': '2', 'ÜÇÜNCÜ': '3',
            'DÖRDÜNCÜ': '4', 'BEŞİNCİ': '5', 'ALTINCI': '6',
            'YEDİNCİ': '7', 'SEKİZİNCİ': '8', 'DOKUZUNCU': '9',
            'ONUNCU': '10'
        }
        
        # Parser state
        self.reset_state()
    
    def reset_state(self):
        """Parser state'ini sıfırla"""
        self.state = {
            'meta': KanunMetadata(),
            'current_kisim': None,
            'current_kisim_basligi': None,
            'current_bolum': None,
            'current_bolum_basligi': None,
            'current_madde': None,
            'chunks': [],
            'current_page': 1,
            'previous_line': None,
            'in_meta_section': True  # İlk sayfada meta bilgiler var
        }
    
    def parse_pdf_text(self, text: str) -> List[Dict]:
        """
        PDF metnini parse et
        
        Args:
            text: PDF'den çıkarılmış tam metin
            
        Returns:
            Chunk'ların listesi
        """
        self.reset_state()
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()            
            
            if not line:
                continue            
            
            self._process_line(line, i, lines)            
            
            self.state['previous_line'] = line        
        
        self._save_current_madde()
        
        return [chunk.to_dict() for chunk in self.state['chunks']]
    
    def _process_line(self, line: str, line_idx: int, all_lines: List[str]):
        """Tek bir satırı işle"""
        
        
        if self.state['in_meta_section']:
            if self._parse_meta_info(line):
                return       
        
        if self._is_page_marker(line):
            return        
        
        if self._parse_kisim(line, all_lines, line_idx):
            return        
       
        if self._parse_bolum(line, all_lines, line_idx):
            return        
        
        if self._parse_madde(line):
            return        
        
        if self._parse_bent(line):
            return        
        
        if self._parse_alt_bent(line):
            return        
        
        self._append_to_current(line)
    
    def _parse_meta_info(self, line: str) -> bool:
        """Meta bilgileri parse et"""        
        
        if not self.state['meta'].kanun_adi and line.isupper() and len(line) < 100:
            if 'KANUN' in line and 'NUMARASI' not in line:
                self.state['meta'].kanun_adi = line
                return True        
        
        match = re.search(self.patterns['kanun_no'], line, re.IGNORECASE)
        if match:
            self.state['meta'].kanun_no = match.group(1)
            return True        
        
        match = re.search(self.patterns['kabul_tarihi'], line, re.IGNORECASE)
        if match:
            self.state['meta'].kabul_tarihi = match.group(1)
            return True        
        
        match = re.search(self.patterns['resmi_gazete'], line, re.IGNORECASE)
        if match:
            self.state['meta'].resmi_gazete_tarihi = match.group(1)
            self.state['meta'].resmi_gazete_sayi = match.group(2)
            return True
                
        if 'KISIM' in line or 'MADDE' in line:
            self.state['in_meta_section'] = False
        
        return False
    
    def _is_page_marker(self, line: str) -> bool:
        """Sayfa işaretçisi mi?"""
        # Basit sayfa tespiti
        if re.match(r'^-+\s*Sayfa\s+\d+\s*-+$', line, re.IGNORECASE):
            return True
        return False
    
    def _parse_kisim(self, line: str, all_lines: List[str], line_idx: int) -> bool:
        """KISIM başlangıcını parse et"""
        match = re.match(self.patterns['kisim'], line)
        if match:
            self.state['current_kisim'] = line
            
            # Bir sonraki satır kısım başlığı
            if line_idx + 1 < len(all_lines):
                next_line = all_lines[line_idx + 1].strip()
                if next_line and not re.match(self.patterns['bolum'], next_line):
                    self.state['current_kisim_basligi'] = next_line
            
            return True
        return False
    
    def _parse_bolum(self, line: str, all_lines: List[str], line_idx: int) -> bool:
        """BÖLÜM başlangıcını parse et"""
        match = re.match(self.patterns['bolum'], line)
        if match:
            self.state['current_bolum'] = line
            
            # Bir sonraki satır bölüm başlığı
            if line_idx + 1 < len(all_lines):
                next_line = all_lines[line_idx + 1].strip()
                if next_line and 'MADDE' not in next_line:
                    self.state['current_bolum_basligi'] = next_line
            
            return True
        return False
    
    def _parse_madde(self, line: str) -> bool:
        """MADDE başlangıcını parse et"""
        match = re.match(self.patterns['madde'], line)
        if match:
            
            self._save_current_madde()            
            
            ek = match.group(1) or ""  # "EK MADDE" ise
            madde_no = match.group(2)            
            
            madde_text = re.sub(self.patterns['madde'], '', line).strip()
            
            self.state['current_madde'] = {
                'no': f"{ek}{madde_no}".strip(),
                'alt_basligi': self.state['previous_line'],  # Bir önceki satır
                'full_text': line,
                'bentler': [],
                'current_bent': None
            }           
            
            bent_match = re.search(self.patterns['bent'], madde_text)
            if bent_match:
                self._parse_bent(madde_text)
            
            return True
        return False
    
    def _parse_bent(self, line: str) -> bool:
        """BENT parse et"""
        if not self.state['current_madde']:
            return False
        
        match = re.match(self.patterns['bent'], line)
        if match:
            bent_no = match.group(1)
            bent_text = match.group(2)            
            
            self.state['current_madde']['current_bent'] = {
                'no': bent_no,
                'text': bent_text,
                'alt_bentler': []
            }
            self.state['current_madde']['bentler'].append(
                self.state['current_madde']['current_bent']
            )
            
            return True
        return False
    
    def _parse_alt_bent(self, line: str) -> bool:
        """ALT BENT parse et"""
        if not self.state['current_madde'] or not self.state['current_madde']['current_bent']:
            return False
        
        match = re.match(self.patterns['alt_bent'], line)
        if match:
            alt_bent_harf = match.group(1)
            alt_bent_text = match.group(2)
            
            self.state['current_madde']['current_bent']['alt_bentler'].append({
                'harf': alt_bent_harf,
                'text': alt_bent_text
            })
            
            return True
        return False
    
    def _append_to_current(self, line: str):
        """Devam eden metni ekle"""
        if not self.state['current_madde']:
            return        
        
        if self.state['current_madde']['current_bent']:
            self.state['current_madde']['current_bent']['text'] += ' ' + line
        else:
            # Bent yoksa madde metnine ekle
            self.state['current_madde']['full_text'] += ' ' + line
    
    def _save_current_madde(self):
        """Mevcut maddeyi chunk olarak kaydet"""
        if not self.state['current_madde']:
            return
        
        madde = self.state['current_madde']        
        
        chunk_text = self._build_chunk_text(madde)        
        
        metadata = ChunkMetadata(
            kanun_adi=self.state['meta'].kanun_adi,
            kanun_no=self.state['meta'].kanun_no,
            kisim=self.state['current_kisim'],
            kisim_basligi=self.state['current_kisim_basligi'],
            bolum=self.state['current_bolum'],
            bolum_basligi=self.state['current_bolum_basligi'],
            madde_no=madde['no'],
            madde_basligi=madde['alt_basligi'],
            bent_sayisi=len(madde['bentler']),
            sayfa_no=self.state['current_page'],
            chunk_id=self._generate_chunk_id(madde['no']),
            token_count=len(chunk_text.split())  # Yaklaşık token sayısı
        )        
        
        chunk = Chunk(text=chunk_text, metadata=metadata)
        self.state['chunks'].append(chunk)        
        
        self.state['current_madde'] = None
    
    def _build_chunk_text(self, madde: Dict) -> str:
        """Madde için tam chunk metni oluştur"""
        lines = []        
        
        if madde['alt_basligi'] and madde['alt_basligi'] not in madde['full_text']:
            lines.append(madde['alt_basligi'])        
        
        lines.append(madde['full_text'])        
        
        for bent in madde['bentler']:
            lines.append(f"({bent['no']}) {bent['text']}")
            
            # Alt bentleri ekle
            for alt_bent in bent.get('alt_bentler', []):
                lines.append(f"  {alt_bent['harf']}) {alt_bent['text']}")
        
        return '\n'.join(lines)
    
    def _generate_chunk_id(self, madde_no: str) -> str:
        """Chunk ID oluştur"""
        
        kanun_adi = self.state['meta'].kanun_adi
        
        if 'İKLİM' in kanun_adi:
            prefix = 'iklim'
        elif 'CEZA' in kanun_adi:
            prefix = 'tck'
        elif 'BORÇLAR' in kanun_adi:
            prefix = 'tbk'
        else:
            prefix = 'kanun'        
        
        madde_clean = madde_no.replace('/', '_').replace(' ', '_').lower()
        
        return f"{prefix}_m{madde_clean}"
    
    def parse_from_file(self, file_path: str) -> List[Dict]:
        """
        Dosyadan parse et (metin dosyası)
        
        Args:
            file_path: Metin dosya yolu
            
        Returns:
            Chunk listesi
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return self.parse_pdf_text(text)
    
    def save_chunks_to_json(self, chunks: List[Dict], output_path: str):
        """Chunk'ları JSON dosyasına kaydet"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        
        print(f"{len(chunks)} chunk kaydedildi: {output_path}")

