# Iris - The Vision That Describes

**🌸 The factual storyteller for auction houses**  
*Reaching the sublime without bathos*

## 👁️ Philosophy

**Iris sees what your viewers cannot see.** We fill the gaps with technical knowledge, contextual anecdotes, and informed storytelling - where fact and narrative merge seamlessly.

**Core Principle**: *How do we reach the sublime without bathos?*  
Through precision, not hyperbole. Through depth, not decoration.

✅ **Multi-modal Image Analysis**: Real visual details from actual auction images  
✅ **Fact-first Content**: Grounded in research, enhanced with subtle storytelling  
✅ **2-Stage Optimized Pipeline**: Research → Direct content generation  
✅ **Single Post Generation**: Eliminated redundant announcement/pre-closing duplication  
✅ **Controlled Creativity**: 80% facticity, 20% narrative flair  

## 📁 Clean Project Structure

```
iris.py                  # 🌸 IRIS: The vision that describes
README.md                # This documentation  
requirements.txt         # Dependencies (includes Pillow for image processing)
.env                     # Configuration (CLAUDE_API_KEY)
posts/                   # Generated content output
archive/                 # All previous versions and experiments
venv/                    # Virtual environment
```

## 🎭 The Evolution: From "Copywriter on Cocaine" to Controlled Facticity

### Before (Narrative Overload):
```
🌟 Ontdek een stukje Nederlandse glorie! 🇳🇱✨

Stel je voor: een exotische vogel zweeft boven een weelderige rode bloem...
Elk penseel streepje fluistert geheimen van verre reizen...
Het is een tijdmachine, een stukje Nederland om elke dag van te genieten.
```

### After (Fact-first with Controlled Flair):
```
Ontdek deze prachtige Makkum Tichelaar Theebus '298', een verfijnd stuk 
Nederlands erfgoed uit de befaamde Tichelaar aardewerkfabriek in Friesland. 
Deze rechthoekige theebus met sierlijke dop is een toonbeeld van 18e/19e-eeuws 
vakmanschap, met een handgeschilderde compositie van een kleurrijke vogel in 
vlucht boven weelderige bloemen in roodtinten.

Tichelaar Makkum, opgericht in 1572, staat bekend om zijn karakteristieke 
polychrome decoraties en is een van de oudste nog bestaande bedrijven in Nederland.
```

## 🚀 Quick Start

1. **Setup Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   pip install -r requirements.txt
   echo "CLAUDE_API_KEY=your_key_here" > .env
   ```

2. **Generate Fact-based Posts**:
   ```bash
   python iris.py --lot LOT_UUID
   ```

3. **Review Output**:
   - Posts saved to `posts/` directory with timestamp
   - Includes detailed research context and visual analysis
   - Single optimized post per lot (no more duplication)

## 🔬 Multi-Modal Research System

**Enhanced Image Analysis**:
- Automatic download and processing of auction images
- Proper headers for API compatibility  
- Image resizing and optimization for Claude vision API
- Extracts actual colors, materials, conditions, and style details

**Research Context**:
- **Historische Significantie**: Factual maker/period information
- **Culturele Context**: Historical usage and societal context  
- **Vakmanschap Details**: Materials, techniques, craftsmanship notes
- **Visuele Analyse**: Detailed description from actual images
- **Lifestyle Scenario**: Practical modern applications
- **Marktpotentieel**: Current collector appeal and value

## 📊 Content Generation Rules

**STRICTE SCHRIJFREGELS**:
1. **START MET FEITEN** - Begin with concrete object identification
2. **VISUELE BESCHRIJVING** - Use ONLY visual analysis, no fictional details  
3. **HISTORISCHE CONTEXT** - Factual information about maker/period
4. **SUBTIELE LIFESTYLE** - Practical modern usage (not poetic)
5. **DIRECTE CALL TO ACTION** - Simple and clear
6. **PRAKTISCHE VRAAG** - About usage or interest, no metaphors

**VERBODEN** (Forbidden):
- Poetic metaphors ("danst", "fluistert", "vertelt verhalen")
- Fictional history ("Gouden Eeuw", "verre reizen")  
- Excessive emotion ("glorie", "meesterwerk", "juweel")
- Time-travel fantasies ("tijdmachine", "geheimen")

**TOEGESTAAN** (Allowed):
- Factual object descriptions
- Historical facts about maker/period
- Practical modern applications  
- Subtle appreciation for craftsmanship

## 🎨 Technical Features

**Image Processing**:
- Downloads images using proper Artisio API headers
- Resizes to 1024x1024 to optimize for Claude vision
- Base64 encoding with JPEG compression
- Retry mechanism for reliable downloads

**Smart Hashtag Generation**:
- Based on research content analysis
- Style/period mapping (Art Deco, Rococo, Mid-Century, etc.)
- Material detection (Mahonie, Zilver, Keramiek, etc.)
- Origin identification (Nederlands, Italiaans, Deens, etc.)

**Error Handling**:
- Graceful fallbacks if image processing fails
- Detailed logging for debugging
- Continues generation even without images

## 🔍 Example Usage

```bash
# Generate post for specific lot UUID
python iris.py --lot 89ab0ed3-16ce-4af9-8b9a-3e8894d009db

# Custom output directory
python iris.py --lot UUID --output custom_posts/
```

## 📈 Key Achievements

1. **Multi-modal Integration**: Real visual analysis from auction images
2. **Balanced Approach**: Facts first, subtle narrative enhancement
3. **Optimized Pipeline**: 2 API calls instead of 3, single post instead of 2
4. **Production Ready**: Clean code, proper error handling, version controlled
5. **Powerful Tool**: Controlled creativity that maintains credibility

## 🏗️ Architecture

```
┌─────────────────────┐    ┌─────────────────────┐
│  EnhancedAI         │    │  ImageProcessor    │
│  Researcher         │◄───┤  (Multi-modal)     │
│                     │    │                     │
└──────────┬──────────┘    └─────────────────────┘
           │
           ▼
┌─────────────────────┐
│  DirectContent      │
│  Generator          │
│  (Fact-first)       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Optimized Social   │
│  Post Output        │
└─────────────────────┘
```

## 📝 Dependencies

- **anthropic**: Claude AI API integration
- **requests**: HTTP requests for API and images
- **python-dotenv**: Environment variable management  
- **Pillow**: Image processing and resizing

---

*🌸 Iris - The Vision That Describes*  
*"Reaching the sublime without bathos through precision, not hyperbole"*