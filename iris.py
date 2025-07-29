import os
import sys
import json
import argparse
import requests
import re
import base64
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from PIL import Image
import io

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
    MODEL_NAME = "claude-3-5-sonnet-20240620"
    def __init__(self, claude_api_key: str):
        self.client = anthropic.Anthropic(api_key=claude_api_key)

    def research_item(self, lot: AuctionLot, image_data: Optional[Dict] = None) -> ResearchContext:
        print(f"🔬 Enhanced Multi-Modal Research for: {lot.title}")
        
        vision_instruction = """
ANALYSEER DE AFBEELDING ZEER GEDETAILLEERD:
- Welke SPECIFIEKE kleuren, materialen en texturen zie je?
- Wat is de staat van het object (nieuw, vintage, slijtage, patina)?
- Welke stijlkenmerken zijn zichtbaar (vormen, decoraties, proporties)?
- Hoe zou dit object er in een moderne woonruimte uitzien?
- Welke emotie of sfeer roept de afbeelding op?
""" if image_data else "Geen afbeelding beschikbaar - focus op tekstuele beschrijving."
        
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
- `visuele_analyse`: ZEER GEDETAILLEERD wat je in de afbeelding ziet - kleuren, staat, sfeer, details (max 3 zinnen)
- `storytelling_hooks`: Array van 2-3 boeiende verhaallijnen/anekdotes over dit object
- `lifestyle_scenario`: Hoe zou een moderne eigenaar dit object gebruiken/presenteren? (max 2 zinnen)

Focus op SPECIFIEKE, VISUELE en EMOTIONELE details die perfect zijn voor social media.
"""

        messages = [{
            "role": "user", 
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": image_data["type"], "data": image_data["data"]}},
                {"type": "text", "text": prompt_text}
            ] if image_data else prompt_text
        }]

        try:
            response = self.client.messages.create(
                model=self.MODEL_NAME, max_tokens=2500, temperature=0.4,
                system="Je bent een expert veilingspecialist die boeiende social media content creëert. Focus op visuele details, verhalen en lifestyle aspecten die het object tot leven brengen.",
                messages=messages
            )
            return self._parse_research_response(response.content[0].text)
        except Exception as e:
            print(f"   ❌ AI Onderzoek mislukt: {e}")
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
    MODEL_NAME = "claude-3-5-sonnet-20240620"
    def __init__(self, claude_api_key: str):
        self.client = anthropic.Anthropic(api_key=claude_api_key)

    def generate_post(self, research: ResearchContext, lot: AuctionLot, auction: Auction) -> str:
        print(f"✍️  Direct post generation using enhanced research...")
        prompt = self._create_content_prompt(research, lot, auction)
        
        try:
            response = self.client.messages.create(
                model=self.MODEL_NAME, max_tokens=1200, temperature=0.6,
                system="Je bent een briljante social media copywriter voor een luxe veilinghuis. Schrijf boeiende, emotionele posts die het object tot leven brengen. Gebruik de toon en structuur van de succesvolle voorbeelden.",
                messages=[{"role": "user", "content": prompt}]
            )
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
"""

# ==============================================================================
#  ENHANCED IMAGE PROCESSING WITH DEBUG & RESIZE
# ==============================================================================
class ImageProcessor:
    @staticmethod
    def process_image_url(url: str, max_size: tuple = (1024, 1024)) -> Optional[Dict]:
        """Download, resize and encode image with detailed debugging."""
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
            
            # Save to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85, optimize=True)
            processed_data = buffer.getvalue()
            
            # Encode to base64
            b64_data = base64.b64encode(processed_data).decode('utf-8')
            print(f"   ✓ Final size: {len(processed_data)} bytes, base64: {len(b64_data)} chars")
            
            return {
                "type": "image/jpeg",
                "data": b64_data
            }
            
        except Exception as e:
            print(f"   ❌ Image processing failed: {e}")
            return None

# ==============================================================================
#  API CLIENT & MAIN ORCHESTRATION
# ==============================================================================
class PublicAPIClient:
    BASE_URL = "https://webapp.artisio.co"
    HEADERS = {
        "Origin": "https://vendulion.com",
        "Referer": "https://vendulion.com/",
        "artisio-client-id": "84528469",
        "artisio-language": "nl"
    }
    
    def get_lot_with_auction(self, lot_uuid: str) -> Optional[Tuple[AuctionLot, Auction]]:
        url = f"{self.BASE_URL}/website/lots/{lot_uuid}"
        print(f"📡 Ophalen kavelgegevens van: {url}")
        
        try:
            response = requests.get(url, headers=self.HEADERS, params={"lot_status": "all"}, timeout=15)
            response.raise_for_status()
            data = response.json()
            
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
            if 'collection_information' in auction_data and auction_data['collection_information'].get('nl'):
                pickup_info = clean_html(auction_data['collection_information']['nl'])
                
            end_date = None
            if auction_data.get('auction_dates') and auction_data['auction_dates'][0].get('end_date'):
                end_date = datetime.fromisoformat(auction_data['auction_dates'][0]['end_date'].replace('Z', '+00:00'))
                
            auction = Auction(
                auction_id=auction_data.get('uuid'),
                title=clean_html(auction_data.get('title', {}).get('nl', 'Veiling niet beschikbaar')),
                end_date=end_date,
                pickup_info=pickup_info
            )
            
            return lot, auction
            
        except requests.RequestException as e:
            print(f"   ❌ API-verzoek mislukt: {e}")
        except (KeyError, IndexError) as e:
            print(f"   ❌ Fout bij parsen: {e}")
        
        return None

class OptimizedSocialAutomation:
    def __init__(self, claude_api_key: str, output_dir: str = "posts"):
        self.researcher = EnhancedAIResearcher(claude_api_key)
        self.content_generator = DirectContentGenerator(claude_api_key)
        self.api_client = PublicAPIClient()
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"✅ Iris initialized. Output to '{self.output_dir}'.")

    def generate_post_for_lot(self, lot_uuid: str):
        """Generate single optimized post for a lot."""
        result = self.api_client.get_lot_with_auction(lot_uuid)
        if not result:
            print(f"Could not retrieve data for lot {lot_uuid}. Aborting.")
            return
            
        lot, auction = result
        print(f"\n--- Iris Generation for: {lot.title} ---")
        
        # Process first image if available
        image_data = None
        if lot.image_urls:
            image_data = ImageProcessor.process_image_url(lot.image_urls[0])
        
        # Enhanced research with vision
        research = self.researcher.research_item(lot, image_data)
        
        # Direct content generation
        final_post = self.content_generator.generate_post(research, lot, auction)
        
        # Save single post
        self._save_post_to_markdown(lot, auction, research, final_post)
        
        print(f"--- Completed Generation for: {lot.title} ---\n")

    def _save_post_to_markdown(self, lot: AuctionLot, auction: Auction, research: ResearchContext, final_post: str):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        safe_title = re.sub(r'[^\w\s-]', '', lot.title).strip().replace(' ', '_')
        filename = f"{timestamp}_iris_{safe_title[:40]}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        end_date_str = auction.end_date.strftime('%d %B %Y, %H:%M uur') if auction.end_date else 'Zie website'
        
        # Generate hashtags based on research
        hashtags = self._generate_smart_hashtags(lot, research)
        
        full_content = f"""# 🌸 Iris Post: {lot.title}

## 🚀 Social Media Post

{final_post}

---

**Veiling:** {auction.title}  
**Sluiting:** 🕰️ {end_date_str}  
**Ophaaldagen:** 📍 {auction.pickup_info}

➡️ **Link in bio!**

{hashtags}

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
*Generated by 🌸 Iris - The Vision That Describes*  
*Lot: {lot.lot_id} | Auction: {auction.auction_id}*
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
        
        # Style/period tags
        style_mapping = {
            "art deco": "#ArtDeco", "rococo": "#Rococo", "barok": "#Barok",
            "mid-century": "#MidCenturyModern", "modernist": "#ModernistDesign",
            "vintage": "#VintageDesign", "antiek": "#Antiek", "klassiek": "#KlassiekDesign"
        }
        
        # Material tags
        material_mapping = {
            "mahonie": "#Mahoniehout", "eiken": "#Eikenhout", "teak": "#TeakHout",
            "zilver": "#Zilver", "brons": "#Brons", "keramiek": "#Keramiek",
            "glas": "#Glas", "kristal": "#Kristal", "porselein": "#Porselein"
        }
        
        # Country/maker tags
        origin_mapping = {
            "nederlands": "#NederlandsDesign", "hollands": "#HollandsAntiek",
            "italiaans": "#ItalianDesign", "deens": "#DeenDesign",
            "zweeds": "#ZweedsDesign", "frans": "#FransDesign"
        }
        
        # Apply mappings
        for mappings in [style_mapping, material_mapping, origin_mapping]:
            for keyword, hashtag in mappings.items():
                if keyword in research_text:
                    tags.add(hashtag)
        
        # Add specific design/furniture tags
        if any(word in research_text for word in ["stoel", "fauteuil", "chair"]):
            tags.add("#DesignStoel")
        if any(word in research_text for word in ["tafel", "table"]):
            tags.add("#DesignTafel")
        if any(word in research_text for word in ["lamp", "verlichting"]):
            tags.add("#DesignVerlichting")
            
        return " ".join(list(tags)[:12])  # Limit to 12 hashtags

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="🌸 Iris - The Vision That Describes")
    parser.add_argument("--lot", required=True, help="UUID of the lot to generate post for")
    parser.add_argument("--output", default="posts", help="Output directory")
    
    args = parser.parse_args()
    
    claude_api_key = os.environ.get("CLAUDE_API_KEY")
    if not claude_api_key:
        print("❌ Error: CLAUDE_API_KEY not found.")
        print("Please create a .env file with CLAUDE_API_KEY=your_key_here")
        sys.exit(1)
        
    automation = OptimizedSocialAutomation(claude_api_key, args.output)
    automation.generate_post_for_lot(args.lot)

if __name__ == "__main__":
    main()