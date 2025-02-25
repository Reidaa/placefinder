import os
from typing import Optional, Set

import cv2
import easyocr
import httpx

from placefinder import console


class MenuAnalyzer:
    """Class for analyzing menu images using OCR"""

    def __init__(self, languages: list[str] = ["en"]):
        """Initialize the OCR reader with specified languages"""
        console.print("[bold blue]Initializing OCR engine...[/]")
        self.reader = easyocr.Reader(languages)
        self.temp_dir = "temp_images"
        os.makedirs(self.temp_dir, exist_ok=True)

    def download_photo(
        self, photo_reference: str, api_key: str, max_width: int = 800
    ) -> Optional[str]:
        """Download a photo from Google Places API and save to temp file"""
        try:
            url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photoreference={photo_reference}&key={api_key}"
            response = httpx.get(url)
            if response.status_code == 200:
                filename = os.path.join(self.temp_dir, f"{photo_reference[:10]}.jpg")
                with open(filename, "wb") as f:
                    f.write(response.content)
                return filename
            return None
        except Exception as e:
            console.print(f"[bold red]Error downloading photo: {str(e)}")
            return None

    def extract_text_from_image(self, image_path: str) -> list[str]:
        """Extract text from an image using EasyOCR"""
        try:
            # Read the image
            image = cv2.imread(image_path)

            # Run OCR
            results = self.reader.readtext(image)

            # Extract text from results
            texts = [text for _, text, conf in results if conf > 0.2]
            return texts
        except Exception as e:
            console.print(f"[bold red]Error extracting text from image: {str(e)}")
            return []

    def find_menu_terms(self, texts: list[str], target_terms: list[str]) -> Set[str]:
        """Find target terms in extracted text"""
        found_terms = set()

        # Convert all text and target terms to lowercase for case-insensitive matching
        texts_lower = [text.lower() for text in texts]
        target_terms_lower = [term.lower() for term in target_terms]

        for term in target_terms_lower:
            # Check for exact matches
            if any(term in text for text in texts_lower):
                found_terms.add(term)

            # Check for terms that might be split across lines
            # This is more complex and might require fuzzy matching
            for i in range(len(texts_lower) - 1):
                combined_text = texts_lower[i] + " " + texts_lower[i + 1]
                if term in combined_text:
                    found_terms.add(term)

        return found_terms

    def analyze_place_photos(
        self, place_id: str, photos: list[dict], api_key: str, target_terms: list[str]
    ) -> list[str]:
        """Analyze photos for a place to find menu terms"""
        found_terms = set()

        # Limit to first 3 photos to reduce API usage and processing time
        for i, photo in enumerate(photos[:3]):
            photo_reference = photo.get("photo_reference")
            if not photo_reference:
                continue

            # Download photo
            image_path = self.download_photo(photo_reference, api_key)
            if not image_path:
                continue

            # Extract text from image
            texts = self.extract_text_from_image(image_path)

            # Find target terms in text
            terms = self.find_menu_terms(texts, target_terms)
            found_terms.update(terms)

            # Remove temporary file
            try:
                os.remove(image_path)
            except:
                pass

        return list(found_terms)
