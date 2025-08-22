import os
import sys
import json
import argparse
import requests
import re
import base64
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from PIL import Image
import io
from cost_analyzer import CostAnalyzer, ModelType, ResearchLevel

# Try to import zoneinfo for proper timezone handling (Python 3.9+)
try:
    from zoneinfo import ZoneInfo
    ZONEINFO_AVAILABLE = True
except ImportError:
    ZONEINFO_AVAILABLE = False

try:
    import anthropic
    from dotenv import load_dotenv
except ImportError:
    print("Error: A required library is not installed. Please run: pip install -r requirements.txt")
    sys.exit(1)

def clean_html(raw_html: str) -> str:
    if not raw_html: return ""
    clean_text = re.sub(r'<[^>]+>', '', raw_html)
    return clean_text.replace('\u00A0', ' ').replace('\xa0', ' ').strip()

def extract_pickup_days(description: str) -> str:
    """Extract pickup days from auction description that contains <b>ophaaldagen:</b> info."""
    if not description:
        return ""
    
    # Look for ophaaldagen pattern (case insensitive)
    pickup_pattern = r'<b>\s*ophaaldagen?\s*:?\s*</b>\s*([^<\n]+)'
    match = re.search(pickup_pattern, description, re.IGNORECASE)
    
    if match:
        pickup_info = match.group(1).strip()
        return f"📅 Ophaaldagen: {pickup_info}"
    
    return ""

def convert_utc_to_dutch_time(utc_datetime: datetime) -> datetime:
    """Convert UTC datetime to Dutch local time (CET/CEST)."""
    if ZONEINFO_AVAILABLE:
        # Use proper timezone handling with zoneinfo
        if utc_datetime.tzinfo is None:
            utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
        elif utc_datetime.tzinfo != timezone.utc:
            utc_datetime = utc_datetime.astimezone(timezone.utc)
        
        amsterdam_tz = ZoneInfo("Europe/Amsterdam")
        return utc_datetime.astimezone(amsterdam_tz)
    else:
        # Fallback: Manual DST calculation
        # Netherlands: UTC+1 (CET) in winter, UTC+2 (CEST) in summer
        # DST roughly: last Sunday in March to last Sunday in October
        
        if utc_datetime.tzinfo is None:
            utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
        
        year = utc_datetime.year
        
        # Calculate DST boundaries (simplified - last Sunday of March and October)
        # This is a rough approximation
        dst_start = datetime(year, 3, 31, 1, 0, 0, tzinfo=timezone.utc)  
        while dst_start.weekday() != 6:  # Sunday = 6
            dst_start = dst_start.replace(day=dst_start.day - 1)
            
        dst_end = datetime(year, 10, 31, 1, 0, 0, tzinfo=timezone.utc)
        while dst_end.weekday() != 6:  # Sunday = 6
            dst_end = dst_end.replace(day=dst_end.day - 1)
        
        # Check if we're in DST period
        if dst_start <= utc_datetime < dst_end:
            # Summer time: UTC+2 (CEST)
            offset = timedelta(hours=2)
        else:
            # Winter time: UTC+1 (CET)
            offset = timedelta(hours=1)
        
        amsterdam_tz = timezone(offset)
        return utc_datetime.astimezone(amsterdam_tz)

# --- Data Models ---
@dataclass
class AuctionLot:
    lot_id: str
    title: str
    description: str = ""
    image_urls: List[str] = None

@dataclass
class Auction:
    auction_id: str
    title: str
    end_date: Optional[datetime] = None
    pickup_info: str = "Zie veilinginformatie in Amstelveen"

@dataclass
class ResearchContext:
    historische_significantie: str
    culturele_context: str
    vakmanschap_details: str
    marktpotentieel: str
    visuele_analyse: str
    storytelling_hooks: List[str]
    lifestyle_scenario: str

# ==============================================================================
#  ENHANCED MULTI-MODAL RESEARCHER
# ==============================================================================
class EnhancedAIResearcher:
    def __init__(self, claude_api_key: str, cost_analyzer: CostAnalyzer = None):
        self.client = anthropic.Anthropic(api_key=claude_api_key)
        self.cost_analyzer = cost_analyzer or CostAnalyzer()
        self.model_name = os.environ.get("RESEARCH_MODEL", "claude-3-5-sonnet-20241022")

    def research_item(self, lot: AuctionLot, primary_image: Optional[Dict] = None, all_images: List[Dict] = None) -> ResearchContext:
        print(f"🔬 Enhanced Multi-Modal Research for: {lot.title}")
        all_images = all_images or []
        
        # Strategy: Primary detailed analysis + supplementary quick analysis
        if primary_image:
            print(f"   🎯 Primary analysis with main image")
            primary_research = self._analyze_primary_image(lot, primary_image)
            
            # If we have additional images, do supplementary analysis
            if len(all_images) > 1:
                print(f"   📸 Supplementary analysis of {len(all_images)-1} additional images")
                supplementary_details = self._analyze_supplementary_images(lot, all_images[1:])
                # Merge findings
                return self._merge_research_findings(primary_research, supplementary_details)
            else:
                return primary_research
        else:
            print(f"   📝 Text-only analysis")
            return self._analyze_text_only(lot)
    
    def _analyze_primary_image(self, lot: AuctionLot, image_data: Dict) -> ResearchContext:
        """Deep analysis of the primary image."""
        vision_instruction = """
ANALYSEER DE AFBEELDING ZEER GEDETAILLEERD:
- Welke SPECIFIEKE kleuren, materialen en texturen zie je?
- Wat is de staat van het object (nieuw, vintage, slijtage, patina)?
- Welke stijlkenmerken zijn zichtbaar (vormen, decoraties, proporties)?
- Hoe zou dit object er in een moderne woonruimte uitzien?
- Welke emotie of sfeer roept de afbeelding op?
- Wat zie je aan details die niet in de beschrijving staan?
"""
        
        # Extract detailed lot information for the prompt
        artist_info = ""
        title_parts = lot.title.split(",") if lot.title else []
        if len(title_parts) >= 2:
            artist_info = f"- **Kunstenaar:** {title_parts[0].strip()}\n"
        
        prompt_text = f"""
Voer diepgaand onderzoek uit naar dit specifieke veilingkavel voor een SOCIAL MEDIA POST.

**EXACTE KAVELGEGEVENS:**
{artist_info}- **Volledige Titel:** {lot.title}
- **Omschrijving/Afmetingen:** {lot.description}
- **Kavel UUID:** {lot.lot_id}

**BELANGRIJKE INSTRUCTIE:** 
Gebruik ALLEEN de bovenstaande EXACTE gegevens. Dit is geen generieke analyse - dit gaat over dit SPECIFIEKE kunstwerk met deze SPECIFIEKE kunstenaar, titel en details.

**VISUELE ANALYSE INSTRUCTIE:**
{vision_instruction}

**ONDERZOEKSTAKEN:**
Creëer een **perfect valide JSON-object** met deze Nederlandse sleutels. Baseer je antwoorden UITSLUITEND op de exacte kavelgegevens hierboven:

- `historische_significantie`: Specifieke informatie over deze kunstenaar en dit exacte werk, gebaseerd op de titel en jaar (max 2 zinnen)
- `culturele_context`: Context specifiek voor dit medium (zeefdruk/grafiek) en deze kunstenaar (max 2 zinnen)  
- `vakmanschap_details`: Details over de zeefdruk techniek en editie-informatie zoals genoemd in de titel (max 2 zinnen)
- `marktpotentieel`: Waarom dit specifieke werk van deze kunstenaar interessant is (max 2 zinnen)
- `visuele_analyse`: ZEER GEDETAILLEERD wat je in de afbeelding ziet - kleuren, compositie, stijl (max 3 zinnen)
- `storytelling_hooks`: Array van 2-3 verhalen specifiek over dit werk of de kunstenaar
- `lifestyle_scenario`: Hoe past dit specifieke grafische werk in een modern interieur (max 2 zinnen)

VERBODEN: Generieke uitspraken over "modern abstract art" of verwijzingen naar andere kunstenaars tenzij relevant voor dit specifieke werk.
"""

        messages = [{
            "role": "user", 
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": image_data["type"], "data": image_data["data"]}},
                {"type": "text", "text": prompt_text}
            ]
        }]

        try:
            response = self.client.messages.create(
                model=self.model_name, max_tokens=2500, temperature=0.4,
                system="Je bent een expert veilingspecialist die boeiende social media content creëert. Focus op visuele details, verhalen en lifestyle aspecten die het object tot leven brengen.",
                messages=messages
            )
            return self._parse_research_response(response.content[0].text)
        except Exception as e:
            print(f"   ❌ Primary analysis failed: {e}")
            return self._create_fallback_context()
    
    def _analyze_supplementary_images(self, lot: AuctionLot, additional_images: List[Dict]) -> str:
        """Quick analysis of additional images to extract extra details."""
        if not additional_images:
            return ""
        
        # Limit to max 3 additional images for cost efficiency
        images_to_analyze = additional_images[:3]
        
        prompt_text = f"""
Analyseer deze aanvullende afbeeldingen van hetzelfde object: {lot.title}

Wat zie je in deze beelden dat EXTRA informatie geeft naast de hoofdafbeelding?
Focus ALLEEN op:
- Nieuwe details die nog niet beschreven zijn
- Andere hoeken/perspectieven die extra informatie geven
- Specifieke onderdelen, mechanismen, decoraties
- Staat/conditie details die niet eerder zichtbaar waren
- Logo's, handtekeningen, stempels die zichtbaar zijn

Geef een korte, feitelijke lijst van de EXTRA details die deze beelden toevoegen.
Vermijd herhaling van informatie uit de hoofdafbeelding.
"""

        # Create message with multiple images
        content = []
        for i, img_data in enumerate(images_to_analyze):
            content.append({
                "type": "image", 
                "source": {
                    "type": "base64", 
                    "media_type": img_data["type"], 
                    "data": img_data["data"]
                }
            })
        content.append({"type": "text", "text": prompt_text})

        messages = [{"role": "user", "content": content}]

        try:
            response = self.client.messages.create(
                model=self.model_name, max_tokens=800, temperature=0.3,
                system="Je bent een expert die extra visuele details extraheert uit aanvullende afbeeldingen. Wees beknopt en specifiek.",
                messages=messages
            )
            return response.content[0].text.strip()
        except Exception as e:
            print(f"   ⚠️ Supplementary analysis failed: {e}")
            return ""
    
    def _analyze_text_only(self, lot: AuctionLot) -> ResearchContext:
        """Fallback text-only analysis."""
        prompt_text = f"""
Voer onderzoek uit naar dit veilingkavel voor een SOCIAL MEDIA POST (alleen op basis van tekst).

**KAVELGEGEVENS:**
- **Titel:** {lot.title}
- **Omschrijving:** {lot.description}

**ONDERZOEKSTAKEN:**
Creëer een **perfect valide JSON-object** met deze Nederlandse sleutels:

- `historische_significantie`: De historische achtergrond, periode, maker/ontwerper (max 2 zinnen)
- `culturele_context`: Maatschappelijke context en gebruik in die tijd (max 2 zinnen)  
- `vakmanschap_details`: Specifieke materialen, technieken, kwaliteitsindicatoren (max 2 zinnen)
- `marktpotentieel`: Waarom dit nu interessant is voor verzamelaars (max 2 zinnen)
- `visuele_analyse`: Beschrijving op basis van titel en omschrijving (max 2 zinnen)
- `storytelling_hooks`: Array van 2-3 boeiende verhaallijnen/anekdotes over dit object
- `lifestyle_scenario`: Hoe zou een moderne eigenaar dit object gebruiken/presenteren? (max 2 zinnen)
"""

        try:
            response = self.client.messages.create(
                model=self.model_name, max_tokens=2000, temperature=0.4,
                system="Je bent een expert veilingspecialist die boeiende social media content creëert op basis van tekstuele informatie.",
                messages=[{"role": "user", "content": prompt_text}]
            )
            return self._parse_research_response(response.content[0].text)
        except Exception as e:
            print(f"   ❌ Text-only analysis failed: {e}")
            return self._create_fallback_context()
    
    def _merge_research_findings(self, primary: ResearchContext, supplementary_details: str) -> ResearchContext:
        """Merge primary research with supplementary visual details."""
        if supplementary_details and supplementary_details.strip():
            # Enhance visual analysis with supplementary details
            enhanced_visual = f"{primary.visuele_analyse} {supplementary_details.strip()}"
            return ResearchContext(
                historische_significantie=primary.historische_significantie,
                culturele_context=primary.culturele_context,
                vakmanschap_details=primary.vakmanschap_details,
                marktpotentieel=primary.marktpotentieel,
                visuele_analyse=enhanced_visual,
                storytelling_hooks=primary.storytelling_hooks,
                lifestyle_scenario=primary.lifestyle_scenario
            )
        return primary
    
    def research_item_with_grid(self, lot: AuctionLot, grid_image_data: Optional[Dict], research_level: ResearchLevel) -> ResearchContext:
        """Simplified research method using grid approach for cost efficiency."""
        print(f"🔬 Grid-based research for: {lot.title} (Level: {research_level.value})")
        
        if research_level == ResearchLevel.BASIC:
            return self._analyze_text_only(lot)
        
        if not grid_image_data:
            print("   📝 No images available, falling back to text-only")
            return self._analyze_text_only(lot)
        
        # Build analysis prompt based on research level
        if research_level == ResearchLevel.COMPREHENSIVE:
            vision_instruction = """
ANALYSEER ALLE AFBEELDINGEN IN DIT GRID ZEER GEDETAILLEERD:
- Beschrijf wat je ziet in elk deel van de grid
- Welke SPECIFIEKE details, kleuren, materialen en texturen zie je?
- Wat is de staat van het object vanuit verschillende hoeken?
- Welke decoratieve elementen, mechanismen, of onderdelen zijn zichtbaar?
- Zijn er logo's, handtekeningen, of merktekens zichtbaar? 
- Welke extra informatie geven de verschillende perspectieven?
- Hoe zou dit object er in een moderne woonruimte uitzien?
"""
        else:  # STANDARD
            vision_instruction = """
ANALYSEER DE AFBEELDING GEDETAILLEERD:
- Welke SPECIFIEKE kleuren, materialen en texturen zie je?
- Wat is de staat van het object?
- Welke stijlkenmerken zijn zichtbaar?
- Hoe zou dit object er in een moderne woonruimte uitzien?
"""
        
        prompt_text = f"""
Voer diepgaand onderzoek uit naar dit veilingkavel voor een SOCIAL MEDIA POST.

**KAVELGEGEVENS:**
- **Titel:** {lot.title}
- **Omschrijving:** {lot.description}

**VISUELE ANALYSE INSTRUCTIE:**
{vision_instruction}

**ONDERZOEKSTAKEN:**
Creëer een **perfect valide JSON-object** met deze Nederlandse sleutels:

- `historische_significantie`: De historische achtergrond, periode, maker/ontwerper (max 2 zinnen)
- `culturele_context`: Maatschappelijke context en gebruik in die tijd (max 2 zinnen)  
- `vakmanschap_details`: Specifieke materialen, technieken, kwaliteitsindicatoren (max 2 zinnen)
- `marktpotentieel`: Waarom dit nu interessant is voor verzamelaars (max 2 zinnen)
- `visuele_analyse`: ZEER GEDETAILLEERD wat je ziet - gebruik alle beschikbare beelden voor een complete beschrijving (max 4 zinnen)
- `storytelling_hooks`: Array van 2-3 boeiende verhaallijnen/anekdotes over dit object
- `lifestyle_scenario`: Hoe zou een moderne eigenaar dit object gebruiken/presenteren? (max 2 zinnen)

Focus op SPECIFIEKE, VISUELE en EMOTIONELE details die perfect zijn voor social media.
"""

        # Build message with image
        content = [
            {"type": "image", "source": {"type": "base64", "media_type": grid_image_data["type"], "data": grid_image_data["data"]}},
            {"type": "text", "text": prompt_text}
        ]
        
        messages = [{"role": "user", "content": content}]

        try:
            response = self.client.messages.create(
                model=self.model_name, 
                max_tokens=2500, 
                temperature=0.4,
                system="Je bent een expert veilingspecialist die boeiende social media content creëert. Focus op visuele details, verhalen en lifestyle aspecten die het object tot leven brengen.",
                messages=messages
            )
            
            # Track costs
            usage = response.usage
            if usage:
                cost_estimate = self.cost_analyzer.track_actual_usage(
                    self.model_name, usage.input_tokens, usage.output_tokens, research_level.value
                )
                print(f"   💰 Cost: ${cost_estimate.total_cost:.4f} ({usage.input_tokens + usage.output_tokens:,} tokens)")
            
            return self._parse_research_response(response.content[0].text)
            
        except Exception as e:
            print(f"   ❌ Grid research failed: {e}")
            return self._create_fallback_context()

    def _parse_research_response(self, response_text: str) -> ResearchContext:
        try:
            json_str = re.search(r'\{.*\}', response_text, re.DOTALL).group(0)
            data = json.loads(json_str)
            return ResearchContext(
                historische_significantie=data.get('historische_significantie', 'N/A'),
                culturele_context=data.get('culturele_context', 'N/A'),
                vakmanschap_details=data.get('vakmanschap_details', 'N/A'),
                marktpotentieel=data.get('marktpotentieel', 'N/A'),
                visuele_analyse=data.get('visuele_analyse', 'Geen visuele analyse beschikbaar'),
                storytelling_hooks=data.get('storytelling_hooks', []),
                lifestyle_scenario=data.get('lifestyle_scenario', 'N/A')
            )
        except (AttributeError, json.JSONDecodeError) as e:
            print(f"   ⚠️ Kon JSON niet parsen ({e}), gebruik fallback.")
            return self._create_fallback_context()
            
    def _create_fallback_context(self) -> ResearchContext:
        return ResearchContext("N/A", "N/A", "N/A", "N/A", "Analyse mislukt.", [], "N/A")

# ==============================================================================
#  DIRECT CONTENT GENERATOR (FACT-FIRST)
# ==============================================================================
class DirectContentGenerator:
    def __init__(self, claude_api_key: str, cost_analyzer: CostAnalyzer = None):
        self.client = anthropic.Anthropic(api_key=claude_api_key)
        self.cost_analyzer = cost_analyzer
        self.model_name = os.environ.get("CONTENT_MODEL", "claude-3-5-sonnet-20241022")

    def generate_post(self, research: ResearchContext, lot: AuctionLot, auction: Auction) -> str:
        print(f"✍️  Direct post generation using enhanced research...")
        prompt = self._create_content_prompt(research, lot, auction)
        
        try:
            response = self.client.messages.create(
                model=self.model_name, max_tokens=1200, temperature=0.6,
                system="Je bent een briljante social media copywriter voor een luxe veilinghuis. Schrijf boeiende, emotionele posts die het object tot leven brengen. Gebruik de toon en structuur van de succesvolle voorbeelden.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Track costs if cost analyzer is available
            if self.cost_analyzer and response.usage:
                cost_estimate = self.cost_analyzer.track_actual_usage(
                    self.model_name, response.usage.input_tokens, response.usage.output_tokens, "content_generation"
                )
                print(f"   💰 Content generation cost: ${cost_estimate.total_cost:.4f} ({response.usage.input_tokens + response.usage.output_tokens:,} tokens)")
            
            return response.content[0].text.strip()
        except Exception as e:
            print(f"   ❌ Content generatie mislukt: {e}")
            return f"Ontdek dit bijzondere stuk: {lot.title} in onze '{auction.title}' veiling."

    def _create_content_prompt(self, research: ResearchContext, lot: AuctionLot, auction: Auction) -> str:
        return f"""
Schrijf een social media post voor dit veilingkavel. PRIORITEIT: FEITEN EERST, subtiele verhalen tweede.

**ONDERZOEKSDATA:**
- **Historisch:** {research.historische_significantie}
- **Cultureel:** {research.culturele_context}
- **Vakmanschap:** {research.vakmanschap_details}
- **Visueel:** {research.visuele_analyse}
- **Lifestyle:** {research.lifestyle_scenario}
- **Marktwaarde:** {research.marktpotentieel}

**KAVEL INFO:**
- **Titel:** {lot.title}
- **Veiling:** {auction.title}

**STRICTE SCHRIJFREGELS:**
1. **START MET FEITEN** - Begin met het concrete object: wat het is, maker, periode
2. **VISUELE BESCHRIJVING** - Gebruik ALLEEN de visuele analyse, geen verzonnen details
3. **HISTORISCHE CONTEXT** - Een feitelijke zin over maker/periode/belang
4. **SUBTIELE LIFESTYLE** - Hoe het object nu gebruikt kan worden (factual, niet poëtisch)
5. **DIRECTE CALL TO ACTION** - Simpel en helder
6. **PRAKTISCHE VRAAG** - Over gebruik of interesse, geen metaforen

**VERBODEN:**
- Poëtische metaforen ("danst", "fluistert", "vertelt verhalen")
- Verzonnen geschiedenis ("Gouden Eeuw", "verre reizen")
- Overdreven emotie ("glorie", "meesterwerk", "juweel")  
- Tijd-reizen fantasieën ("tijdmachine", "geheimen")

**TOEGESTAAN:**
- Feitelijke beschrijvingen van het object
- Historische feiten over maker/periode
- Praktische moderne toepassingen
- Subtiele waardering voor vakmanschap

**TOON:** Informatief, respectvol enthousiast, gebaseerd op feiten.
**LENGTE:** 2-3 paragrafen, direct en helder.
**FORMATTING:** Schrijf PLATTE TEKST zonder markdown opmaak (geen **, ##, of andere markdown codes).
"""

# ==============================================================================
#  ENHANCED IMAGE PROCESSING WITH DEBUG & RESIZE
# ==============================================================================
class ImageProcessor:
    @staticmethod
    def process_image_url(url: str, lot_title: str = "", max_size: tuple = (1024, 1024), save_local: bool = True) -> Optional[Dict]:
        """Download, resize and encode image with detailed debugging and local saving."""
        print(f"🖼️ Processing image: {url}")
        
        try:
            # Use same headers as API calls for consistency
            image_headers = {
                "Origin": "https://vendulion.com",
                "Referer": "https://vendulion.com/",
                "artisio-client-id": "84528469",
                "artisio-language": "nl",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            # Download with retries
            for attempt in range(3):
                try:
                    response = requests.get(url, headers=image_headers, timeout=15, stream=True)
                    response.raise_for_status()
                    break
                except requests.RequestException as e:
                    print(f"   ⚠️ Attempt {attempt + 1} failed: {e}")
                    if attempt == 2:
                        return None
            
            # Process image
            image_data = response.content
            print(f"   ✓ Downloaded {len(image_data)} bytes")
            
            # Open and resize image
            image = Image.open(io.BytesIO(image_data))
            original_format = image.format
            print(f"   ✓ Original: {image.size} {original_format}")
            
            # Resize if needed
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                print(f"   ✓ Resized to: {image.size}")
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save locally if requested
            local_path = None
            if save_local and lot_title:
                local_path = ImageProcessor._save_image_locally(image, lot_title)
            
            # Save to bytes for API
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85, optimize=True)
            processed_data = buffer.getvalue()
            
            # Encode to base64
            b64_data = base64.b64encode(processed_data).decode('utf-8')
            print(f"   ✓ Final size: {len(processed_data)} bytes, base64: {len(b64_data)} chars")
            
            result = {
                "type": "image/jpeg",
                "data": b64_data
            }
            
            if local_path:
                result["local_path"] = local_path
            
            return result
            
        except Exception as e:
            print(f"   ❌ Image processing failed: {e}")
            return None
    
    @staticmethod
    def create_image_grid(images: List[Image.Image], grid_size: tuple = (2, 2), output_size: tuple = (1024, 1024)) -> Image.Image:
        """Create a grid of images for efficient multi-image analysis."""
        cols, rows = grid_size
        cell_width = output_size[0] // cols
        cell_height = output_size[1] // rows
        
        # Create blank grid
        grid = Image.new('RGB', output_size, (255, 255, 255))
        
        for i, img in enumerate(images[:cols*rows]):  # Limit to grid capacity
            if img is None:
                continue
                
            row = i // cols
            col = i % cols
            
            # Resize image to fit cell
            img_resized = img.copy()
            img_resized.thumbnail((cell_width-10, cell_height-10), Image.Resampling.LANCZOS)
            
            # Calculate position (centered in cell)
            x_offset = col * cell_width + (cell_width - img_resized.width) // 2
            y_offset = row * cell_height + (cell_height - img_resized.height) // 2
            
            grid.paste(img_resized, (x_offset, y_offset))
        
        return grid
    
    @staticmethod
    def process_multiple_images_individually(urls: List[str], lot_title: str, max_images: int = 4) -> Tuple[Optional[Dict], List[str]]:
        """Process multiple images and save them individually for Meta upload."""
        print(f"📸 Processing {min(len(urls), max_images)} individual images for Meta upload")
        
        processed_images = []
        local_image_paths = []
        successful_downloads = 0
        
        for i, url in enumerate(urls[:max_images]):
            print(f"   Downloading image {i+1}/{min(len(urls), max_images)}")
            try:
                # Use the existing process_image_url function which already saves locally
                unique_title = f"{lot_title}_img{i+1:02d}"
                image_data = ImageProcessor.process_image_url(
                    url, 
                    unique_title,  # Add zero-padded numbering
                    save_local=True
                )
                
                if image_data:
                    processed_images.append(image_data)
                    if 'local_path' in image_data:
                        local_image_paths.append(image_data['local_path'])
                    successful_downloads += 1
                    
            except Exception as e:
                print(f"   ⚠️ Failed to process image {i+1}: {e}")
        
        if successful_downloads == 0:
            return None, []
        
        print(f"   ✅ Successfully processed {successful_downloads} individual images")
        
        # For API analysis, we can still create a grid from the first image or use the first image
        primary_image_data = processed_images[0] if processed_images else None
        
        return primary_image_data, local_image_paths

    @staticmethod
    def process_multiple_images_as_grid(urls: List[str], lot_title: str, max_images: int = 4) -> Optional[Dict]:
        """Process multiple images and create a grid for efficient analysis."""
        print(f"🎯 Creating image grid from {min(len(urls), max_images)} images")
        
        images = []
        successful_downloads = 0
        
        for i, url in enumerate(urls[:max_images]):
            print(f"   Downloading image {i+1}/{min(len(urls), max_images)}")
            try:
                # Download image
                image_headers = {
                    "Origin": "https://vendulion.com",
                    "Referer": "https://vendulion.com/",
                    "artisio-client-id": "84528469",
                    "artisio-language": "nl",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                }
                
                response = requests.get(url, headers=image_headers, timeout=15, stream=True)
                response.raise_for_status()
                
                image = Image.open(io.BytesIO(response.content))
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                images.append(image)
                successful_downloads += 1
                
            except Exception as e:
                print(f"   ⚠️ Failed to download image {i+1}: {e}")
                images.append(None)
        
        if successful_downloads == 0:
            return None
        
        # Determine grid size based on number of images
        if successful_downloads == 1:
            grid_size = (1, 1)
        elif successful_downloads <= 2:
            grid_size = (2, 1)
        elif successful_downloads <= 4:
            grid_size = (2, 2)
        else:
            grid_size = (3, 2)
        
        # Create grid
        grid_image = ImageProcessor.create_image_grid(images, grid_size)
        
        # Save grid locally
        local_path = ImageProcessor._save_image_locally(grid_image, f"{lot_title}_grid")
        
        # Convert to base64 for API
        buffer = io.BytesIO()
        grid_image.save(buffer, format='JPEG', quality=85, optimize=True)
        processed_data = buffer.getvalue()
        b64_data = base64.b64encode(processed_data).decode('utf-8')
        
        print(f"   ✅ Grid created: {grid_size[0]}x{grid_size[1]}, {len(processed_data):,} bytes")
        
        return {
            "type": "image/jpeg",
            "data": b64_data,
            "local_path": local_path,
            "grid_info": {
                "size": grid_size,
                "images_count": successful_downloads,
                "total_attempted": min(len(urls), max_images)
            }
        }

    @staticmethod
    def _save_image_locally(image: Image.Image, lot_title: str) -> str:
        """Save image to local images folder with appropriate naming."""
        try:
            # Create images directory if it doesn't exist
            os.makedirs("images", exist_ok=True)
            
            # Clean lot title for filename
            safe_title = re.sub(r'[^\w\s-]', '', lot_title).strip().replace(' ', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")  # Include microseconds for uniqueness
            filename = f"{timestamp}_{safe_title[:40]}.jpg"
            filepath = os.path.join("images", filename)
            
            # Save image
            image.save(filepath, format='JPEG', quality=90, optimize=True)
            print(f"   💾 Image saved locally: {filepath}")
            
            return filepath
            
        except Exception as e:
            print(f"   ⚠️ Could not save image locally: {e}")
            return None

# ==============================================================================
#  API CLIENT & MAIN ORCHESTRATION
# ==============================================================================
class PublicAPIClient:
    def __init__(self):
        self.BASE_URL = os.environ.get("API_BASE_URL", "https://webapp.artisio.co")
        origin_url = os.environ.get("ORIGIN_URL", "https://vendulion.com")
        
        self.HEADERS = {
            "accept": os.environ.get("ACCEPT_HEADER", "application/json, text/plain, */*"),
            "accept-encoding": os.environ.get("ACCEPT_ENCODING_HEADER", "gzip, deflate, br, zstd"),
            "accept-language": os.environ.get("ACCEPT_LANGUAGE_HEADER", "en-GB,en;q=0.7"),
            "artisio-client-id": os.environ.get("ARTISIO_CLIENT_ID", "84528469"),
            "artisio-language": os.environ.get("ARTISIO_LANGUAGE", "nl"),
            "origin": origin_url,
            "referer": f"{origin_url}/",
            "sec-ch-ua": os.environ.get("SEC_CH_UA_HEADER", '"Not;A=Brand";v="99", "Brave";v="139", "Chromium";v="139"'),
            "sec-ch-ua-mobile": os.environ.get("SEC_CH_UA_MOBILE_HEADER", "?0"),
            "sec-ch-ua-platform": os.environ.get("SEC_CH_UA_PLATFORM_HEADER", '"macOS"'),
            "sec-fetch-dest": os.environ.get("SEC_FETCH_DEST_HEADER", "empty"),
            "sec-fetch-mode": os.environ.get("SEC_FETCH_MODE_HEADER", "cors"),
            "sec-fetch-site": os.environ.get("SEC_FETCH_SITE_HEADER", "cross-site"),
            "sec-gpc": os.environ.get("SEC_GPC_HEADER", "1"),
            "user-agent": os.environ.get("USER_AGENT_HEADER", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36")
        }
    
    def get_lot_with_auction(self, uuid: str) -> Optional[Tuple[AuctionLot, Auction]]:
        # Try as auction first (more common case based on the example)
        auction_url = f"{self.BASE_URL}{os.environ.get('AUCTION_ENDPOINT', '/website/auctions/timed')}/{uuid}"
        print(f"📡 Trying auction endpoint: {auction_url}")
        
        try:
            response = requests.get(auction_url, headers=self.HEADERS, timeout=15)
            if response.status_code == 200 and response.content:
                return self._parse_auction_response(response.json(), uuid)
        except (requests.RequestException, ValueError) as e:
            print(f"   Auction endpoint failed: {e}")
        
        # Try as lot if auction fails
        lot_url = f"{self.BASE_URL}{os.environ.get('LOT_ENDPOINT', '/website/lots')}/{uuid}"
        print(f"📡 Trying lot endpoint: {lot_url}")
        
        try:
            response = requests.get(lot_url, headers=self.HEADERS, params={"lot_status": "all"}, timeout=15)
            if response.status_code == 200:
                return self._parse_lot_response(response.json())
        except requests.RequestException:
            pass
        
        print(f"   ❌ Could not find data for UUID {uuid} in either endpoint")
        return None
    
    def _parse_auction_response(self, data: dict, auction_uuid: str) -> Optional[Tuple[AuctionLot, Auction]]:
        """Parse auction data - for now, return first lot or create placeholder"""
        try:
            # Create auction object from auction data
            pickup_info = "Zie veilinginformatie in Amstelveen"
            if 'collection_information' in data and data['collection_information'].get('nl'):
                pickup_info = clean_html(data['collection_information']['nl'])
            elif 'description' in data and data['description'].get('nl'):
                pickup_info = clean_html(data['description']['nl'])
                
            end_date = None
            if data.get('auction_dates') and data['auction_dates'][0].get('end_date'):
                end_date = datetime.fromisoformat(data['auction_dates'][0]['end_date'].replace('Z', '+00:00'))
                
            auction = Auction(
                auction_id=data.get('uuid'),
                title=clean_html(data.get('title', {}).get('nl', 'Veiling niet beschikbaar')),
                end_date=end_date,
                pickup_info=pickup_info
            )
            
            # Create a placeholder lot representing the entire auction
            lot = AuctionLot(
                lot_id=auction_uuid,
                title=f"Veiling: {auction.title}",
                description=clean_html(data.get('description', {}).get('nl', '')),
                image_urls=[
                    (img.get('lg', {}).get('url') if isinstance(img.get('lg'), dict) else img.get('lg')) or
                    (img.get('original', {}).get('url') if isinstance(img.get('original'), dict) else img.get('original')) or
                    (img.get('xlg', {}).get('url') if isinstance(img.get('xlg'), dict) else img.get('xlg'))
                    for img in data.get('images', [])
                    if (img.get('lg') and (img.get('lg', {}).get('url') if isinstance(img.get('lg'), dict) else img.get('lg'))) or
                       (img.get('original') and (img.get('original', {}).get('url') if isinstance(img.get('original'), dict) else img.get('original'))) or
                       (img.get('xlg') and (img.get('xlg', {}).get('url') if isinstance(img.get('xlg'), dict) else img.get('xlg')))
                ]
            )
            
            return lot, auction
            
        except (KeyError, IndexError) as e:
            print(f"   ❌ Fout bij parsen auction data: {e}")
            return None
    
    def _parse_lot_response(self, data: dict) -> Optional[Tuple[AuctionLot, Auction]]:
        """Parse individual lot data"""
        try:
            lot_data, auction_data = data, data.get('auction', {})
            
            lot = AuctionLot(
                lot_id=lot_data.get('uuid'), 
                title=clean_html(lot_data.get('title', {}).get('nl', 'Titel niet beschikbaar')), 
                description=clean_html(lot_data.get('description', {}).get('nl', '')),
                image_urls=[
                    (img.get('lg', {}).get('url') if isinstance(img.get('lg'), dict) else img.get('lg')) or
                    (img.get('original', {}).get('url') if isinstance(img.get('original'), dict) else img.get('original')) or
                    (img.get('xlg', {}).get('url') if isinstance(img.get('xlg'), dict) else img.get('xlg'))
                    for img in lot_data.get('images', [])
                    if (img.get('lg') and (img.get('lg', {}).get('url') if isinstance(img.get('lg'), dict) else img.get('lg'))) or
                       (img.get('original') and (img.get('original', {}).get('url') if isinstance(img.get('original'), dict) else img.get('original'))) or
                       (img.get('xlg') and (img.get('xlg', {}).get('url') if isinstance(img.get('xlg'), dict) else img.get('xlg')))
                ]
            )
            
            pickup_info = "Zie veilinginformatie in Amstelveen"
            
            # First, try to extract pickup days from auction description
            auction_description = auction_data.get('description', {}).get('nl', '')
            pickup_days = extract_pickup_days(auction_description)
            
            # Get pickup location info
            pickup_location = ""
            
            # Try collection_information first
            if 'collection_information' in auction_data and auction_data['collection_information'].get('nl'):
                pickup_location = clean_html(auction_data['collection_information']['nl'])
            
            # If no auction pickup location, try lot-level collection_info
            elif 'collection_info' in data and data['collection_info']:
                collection_info = data['collection_info']
                address_parts = []
                
                if collection_info.get('address_1'):
                    address_parts.append(collection_info['address_1'])
                if collection_info.get('city'):
                    address_parts.append(collection_info['city'])
                
                if address_parts:
                    pickup_location = f"📍 {', '.join(address_parts)}"
            
            # Combine pickup days and location
            if pickup_days and pickup_location:
                pickup_info = f"{pickup_days}\n{pickup_location}"
            elif pickup_days:
                pickup_info = pickup_days
            elif pickup_location:
                pickup_info = pickup_location
                
            end_date = None
            if auction_data.get('auction_dates') and auction_data['auction_dates'][0].get('end_date'):
                utc_end_date = datetime.fromisoformat(auction_data['auction_dates'][0]['end_date'].replace('Z', '+00:00'))
                end_date = convert_utc_to_dutch_time(utc_end_date)
                
            auction = Auction(
                auction_id=auction_data.get('uuid'),
                title=clean_html(auction_data.get('title', {}).get('nl', 'Veiling niet beschikbaar')),
                end_date=end_date,
                pickup_info=pickup_info
            )
            
            return lot, auction
            
        except (KeyError, IndexError) as e:
            print(f"   ❌ Fout bij parsen lot data: {e}")
            return None

class OptimizedSocialAutomation:
    def __init__(self, claude_api_key: str, output_dir: str = "posts", research_level: ResearchLevel = ResearchLevel.COMPREHENSIVE):
        self.cost_analyzer = CostAnalyzer()
        self.researcher = EnhancedAIResearcher(claude_api_key, self.cost_analyzer)
        self.content_generator = DirectContentGenerator(claude_api_key, self.cost_analyzer)
        self.api_client = PublicAPIClient()
        self.output_dir = output_dir
        self.research_level = research_level
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"✅ Iris initialized. Output to '{self.output_dir}'. Research level: {research_level.value}")

    def generate_post_for_lot(self, lot_uuid: str):
        """Generate single optimized post for a lot."""
        result = self.api_client.get_lot_with_auction(lot_uuid)
        if not result:
            print(f"Could not retrieve data for lot {lot_uuid}. Aborting.")
            return
            
        lot, auction = result
        print(f"\n--- Iris Generation for: {lot.title} ---")
        
        # Process images based on research level
        grid_image_data = None
        local_image_paths = []
        
        if lot.image_urls and self.research_level != ResearchLevel.BASIC:
            if self.research_level == ResearchLevel.COMPREHENSIVE:
                # Use efficient grid approach for AI analysis
                grid_image_data = ImageProcessor.process_multiple_images_as_grid(
                    lot.image_urls, lot.title, max_images=4
                )
                print(f"   💰 Grid approach: 1 API call for {grid_image_data.get('grid_info', {}).get('images_count', 0) if grid_image_data else 0} images")
                
                # Also save individual images for Meta upload
                _, individual_image_paths = ImageProcessor.process_multiple_images_individually(
                    lot.image_urls, lot.title, max_images=4
                )
                local_image_paths.extend(individual_image_paths)
                print(f"   📱 Individual images ready for Meta: {len(individual_image_paths)} files")
            
            elif self.research_level == ResearchLevel.STANDARD:
                # Single image approach for AI, but still save individuals for Meta
                if lot.image_urls:
                    grid_image_data = ImageProcessor.process_image_url(lot.image_urls[0], f"{lot.title}_primary")
                    
                    # Save individual images for Meta
                    _, individual_image_paths = ImageProcessor.process_multiple_images_individually(
                        lot.image_urls, lot.title, max_images=4
                    )
                    local_image_paths.extend(individual_image_paths)
                    print(f"   📱 Individual images ready for Meta: {len(individual_image_paths)} files")
            
            elif self.research_level == ResearchLevel.PREMIUM:
                # Individual image processing (most expensive for AI)
                print("⚠️ Premium mode: Processing images individually for AI (high cost)")
                primary_image_data, individual_image_paths = ImageProcessor.process_multiple_images_individually(
                    lot.image_urls, lot.title, max_images=4
                )
                grid_image_data = primary_image_data
                local_image_paths.extend(individual_image_paths)
                print(f"   📱 Individual images ready for Meta: {len(individual_image_paths)} files")
        
        # Enhanced research with vision
        research = self.researcher.research_item_with_grid(lot, grid_image_data, self.research_level)
        
        # Direct content generation
        final_post = self.content_generator.generate_post(research, lot, auction)
        
        # Save single post
        self._save_post_to_markdown(lot, auction, research, final_post, local_image_paths)
        
        # Display cost summary
        session_cost = self.cost_analyzer.get_session_total()
        if session_cost > 0:
            print(f"💰 Session cost so far: ${session_cost:.4f}")
        
        print(f"--- Completed Generation for: {lot.title} ---\n")

    def _save_post_to_markdown(self, lot: AuctionLot, auction: Auction, research: ResearchContext, final_post: str, local_image_paths: List[str] = None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        safe_title = re.sub(r'[^\w\s-]', '', lot.title).strip().replace(' ', '_')
        filename = f"{timestamp}_iris_{safe_title[:40]}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        end_date_str = auction.end_date.strftime('%d %B %Y, %H:%M uur') if auction.end_date else 'Zie website'
        
        # Generate hashtags based on research
        hashtags = self._generate_smart_hashtags(lot, research)
        
        # Format pickup info for the new structure
        pickup_display = auction.pickup_info.replace('📅 Ophaaldagen: ', '').replace('📍 ', '')
        if '\n' in pickup_display:
            # Split pickup days and location
            lines = pickup_display.split('\n')
            pickup_days = lines[0]
            pickup_location = lines[1] if len(lines) > 1 else 'Amstelveen'
        else:
            pickup_days = pickup_display
            pickup_location = 'Amstelveen'
        
        # Remove #linkinbio from hashtags since we'll put it with "Link in bio"
        hashtags_clean = hashtags.replace('#linkinbio', '').strip()
        
        full_content = f"""# 🌸 Iris Post: {lot.title}

## 🚀 Social Media Post

{final_post}

➡️ Link in bio! #linkinbio

Veiling: {auction.title}
🕰️ Sluiting: {end_date_str.replace(' uur', '')}
📍 Ophaaldagen: {pickup_days} in {pickup_location}

{hashtags_clean}

---

## 🧠 Enhanced Research Context

**Historische Significantie:** {research.historische_significantie}

**Culturele Context:** {research.culturele_context}

**Vakmanschap:** {research.vakmanschap_details}

**Visuele Analyse:** {research.visuele_analyse}

**Lifestyle Scenario:** {research.lifestyle_scenario}

**Storytelling Hooks:**
{"; ".join([f"- {hook}" for hook in research.storytelling_hooks]) if research.storytelling_hooks else "Geen hooks beschikbaar"}

**Marktpotentieel:** {research.marktpotentieel}

---

## 📸 Downloaded Images

{chr(10).join([f"- `{path}`" for path in (local_image_paths or [])]) if local_image_paths else "No images downloaded"}

---
*Generated by 🌸 Iris - The Vision That Describes*  
*Research Level: {self.research_level.value} | Lot: {lot.lot_id} | Auction: {auction.auction_id}*
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)
        print(f"💾 Post saved to: {filepath}")
    
    def _generate_smart_hashtags(self, lot: AuctionLot, research: ResearchContext) -> str:
        """Generate intelligent hashtags based on research context."""
        tags = set(["#Veiling", "#BiedenMaar", "#Amstelveen"])
        
        # Add tags based on research content
        research_text = (research.historische_significantie + " " + 
                        research.culturele_context + " " + 
                        research.vakmanschap_details + " " +
                        lot.title).lower()
        
        # Core category tags - always include antiek
        if any(word in research_text for word in ["antiek", "historisch", "vintage", "oud"]):
            tags.add("#Antiek")
        
        # Historical period tags
        period_mapping = {
            "victoriaans": "#Victoriaans", "art nouveau": "#ArtNouveau", "art deco": "#ArtDeco",
            "rococo": "#Rococo", "barok": "#Barok", "biedermeier": "#Biedermeier",
            "mid-century": "#MidCenturyModern", "modernist": "#ModernistDesign",
            "17e eeuw": "#17eEeuw", "18e eeuw": "#18eEeuw", "19e eeuw": "#19eEeuw",
            "20e eeuw": "#20eEeuw", "gouden eeuw": "#GoudenEeuw"
        }
        
        # Material and technique tags
        material_mapping = {
            "mahonie": "#Mahoniehout", "eiken": "#Eikenhout", "teak": "#TeakHout", "hout": "#Hout",
            "zilver": "#Zilver", "goud": "#Goud", "brons": "#Brons", "messing": "#Messing",
            "keramiek": "#Keramiek", "porselein": "#Porselein", "aardewerk": "#Aardewerk",
            "glas": "#Glas", "kristal": "#Kristal", "lood": "#Loodkristal",
            "intarsia": "#Intarsia", "fineer": "#Fineer", "inlegwerk": "#Inlegwerk"
        }
        
        # Origin and maker tags
        origin_mapping = {
            "nederlands": "#NederlandsDesign", "hollands": "#HollandsAntiek", "amsterdam": "#Amsterdam",
            "italiaans": "#ItalianDesign", "deens": "#DeenDesign", "zweeds": "#ZweedsDesign",
            "frans": "#FransDesign", "duits": "#DuitsDesign", "engels": "#EngelsDesign",
            "leeuwarden": "#Leeuwarden", "delft": "#Delft"
        }
        
        # Functional category tags
        function_mapping = {
            "stoel": "#DesignStoel", "fauteuil": "#Fauteuil", "chair": "#DesignStoel",
            "tafel": "#DesignTafel", "table": "#DesignTafel", "bureau": "#Bureau",
            "lamp": "#DesignVerlichting", "verlichting": "#DesignVerlichting", "kroonluchter": "#Kroonluchter",
            "kast": "#DesignKast", "ladekast": "#Ladekast", "boekenkast": "#Boekenkast",
            "spiegel": "#AntiekeSpiegel", "klok": "#AntiekeKlok", "pendule": "#Pendule",
            "vaas": "#AntiekeVaas", "schaal": "#AntiekeSchaal", "schaaltje": "#Schaaltje",
            "speeldoos": "#Speeldoos", "muziekinstrument": "#MuziekInstrument", "muziekdoos": "#Muziekdoos"
        }
        
        # Collector and interest tags
        collector_mapping = {
            "verzamelaar": "#Verzamelaar", "collectie": "#Collectie", "zeldzaam": "#ZeldzaamItem",
            "uniek": "#UniekItem", "limited": "#LimitedEdition", "handgemaakt": "#Handgemaakt",
            "kunstwerk": "#Kunstwerk", "meesterwerk": "#Meesterwerk"
        }
        
        # Interior style tags
        interior_mapping = {
            "vintage": "#VintageInterieur", "klassiek": "#KlassiekInterieur", "modern": "#ModernInterieur",
            "industrieel": "#IndustrieelInterieur", "shabby": "#ShabbyChic", "landelijk": "#LandelijkInterieur"
        }
        
        # Apply all mappings
        all_mappings = [period_mapping, material_mapping, origin_mapping, function_mapping, collector_mapping, interior_mapping]
        for mapping in all_mappings:
            for keyword, hashtag in mapping.items():
                if keyword in research_text:
                    tags.add(hashtag)
        
        # Add specialty tags based on context
        if "mechanisch" in research_text:
            tags.add("#MechanischeMuziek")
        if "historisch" in research_text:
            tags.add("#Historisch")
        if "zeldzaam" in research_text or "uniek" in research_text:
            tags.add("#UniekItem")
        if "vakmanschap" in research_text or "ambacht" in research_text:
            tags.add("#Vakmanschap")
        if "investering" in research_text or "waarde" in research_text:
            tags.add("#Investering")
        
        # Extract designer/artist and manufacturer names for hashtags
        designer_manufacturer_mapping = {
            # Designers/Artists
            "polyphon": "#Polyphon", "regina": "#Regina", "symphonion": "#Symphonion",
            "thonet": "#Thonet", "knoll": "#Knoll", "herman miller": "#HermanMiller",
            "gispen": "#Gispen", "rietveld": "#Rietveld", "berlage": "#Berlage",
            "van der waals": "#VanDerWaals", "de bazel": "#DeBazel",
            
            # Manufacturers/Workshops  
            "hollandia": "#Hollandia", "zilversmederij": "#Zilversmederij",
            "van eldrik": "#VanEldrik", "b.w. van eldrik": "#BWVanEldrik",
            "royal delft": "#RoyalDelft", "de porceleyne fles": "#DePorcelyneFiles",
            "kristalunie": "#Kristalunie", "leerdam": "#Leerdam",
            "philips": "#Philips", "artifort": "#Artifort", "pastoe": "#Pastoe",
            
            # Pottery/Ceramics makers
            "plateelbakkerij": "#Plateelbakkerij", "pottenbakkerij": "#Pottenbakkerij",
            "aardewerk": "#Aardewerk", "keramiek": "#Keramiek",
            
            # Clock makers
            "warmink": "#Warmink", "hermle": "#Hermle", "kieninger": "#Kieninger",
            "junghans": "#Junghans", "gustav becker": "#GustavBecker",
            
            # Furniture makers
            "pastoe": "#Pastoe", "artifort": "#Artifort", "spectrum": "#Spectrum",
            "cassina": "#Cassina", "vitra": "#Vitra"
        }
        
        # Apply designer/manufacturer mapping
        for keyword, hashtag in designer_manufacturer_mapping.items():
            if keyword in research_text:
                tags.add(hashtag)
        
        # Extract proper names from title and research for custom hashtags
        # Look for capitalized words that might be makers/designers
        import re
        # Find potential maker names (patterns like "B.W. van Eldrik", "Herman Miller", etc.)
        maker_patterns = [
            r'\b[A-Z]\.[A-Z]\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # B.W. van Eldrik
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'     # Herman Miller, Royal Delft
        ]
        
        full_text = lot.title + " " + research.historische_significantie + " " + research.culturele_context
        for pattern in maker_patterns:
            matches = re.findall(pattern, full_text)
            for match in matches:
                # Convert to hashtag format (remove spaces and dots)
                hashtag_name = re.sub(r'[.\s]+', '', match)
                if len(hashtag_name) > 2 and len(hashtag_name) < 25:  # Reasonable length
                    tags.add(f"#{hashtag_name}")
        
        # Convert to sorted list and limit to 25 hashtags (increased for more coverage)
        final_tags = sorted(list(tags))[:25]
        return " ".join(final_tags)

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="🌸 Iris - The Vision That Describes")
    parser.add_argument("--lot", help="UUID of the lot to generate post for")
    parser.add_argument("--output", default="posts", help="Output directory")
    parser.add_argument("--research-level", choices=["basic", "standard", "comprehensive", "premium"], 
                       default="comprehensive", help="Research intensity level (default: comprehensive)")
    parser.add_argument("--cost-analysis", action="store_true", help="Generate cost analysis report")
    parser.add_argument("--budget-lots", type=int, default=100, help="Number of lots for budget analysis (default: 100)")
    
    args = parser.parse_args()
    
    # Handle cost analysis mode
    if args.cost_analysis:
        print("💰 Generating cost analysis...")
        analyzer = CostAnalyzer()
        report = analyzer.generate_budget_report(args.budget_lots)
        
        with open("iris_cost_analysis.md", "w") as f:
            f.write(report)
        
        print("✅ Cost analysis saved to 'iris_cost_analysis.md'")
        
        # Also run the cost analyzer main function for CLI output
        from cost_analyzer import main as cost_main
        cost_main()
        return
    
    if not args.lot:
        print("❌ Error: --lot is required unless using --cost-analysis")
        parser.print_help()
        sys.exit(1)
    
    claude_api_key = os.environ.get("CLAUDE_API_KEY")
    if not claude_api_key:
        print("❌ Error: CLAUDE_API_KEY not found.")
        print("Please create a .env file with CLAUDE_API_KEY=your_key_here")
        sys.exit(1)
    
    # Convert string to enum
    research_level = ResearchLevel(args.research_level)
    
    print(f"🌸 Iris starting with {research_level.value} research level")
    automation = OptimizedSocialAutomation(claude_api_key, args.output, research_level)
    automation.generate_post_for_lot(args.lot)
    
    # Save cost report
    automation.cost_analyzer.save_session_report(f"cost_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json")

if __name__ == "__main__":
    main()