import tempfile
from pathlib import Path

import cv2
import easyocr
import httpx

from placefinder.env import env
from placefinder.t import PlacePhoto


class VisualAnalyzer:
    """Class for analyzing images using OCR"""

    def __init__(self, languages: list[str] = ["en"]):
        self.reader = easyocr.Reader(languages)
        self.temp = tempfile.TemporaryDirectory()
        self.temp_dir = self.temp.name

    def download_photo(self, photo_reference: str, max_width: int = 800) -> str:
        """
        Download a photo from Google Places API and save to temp file

        Raises:
            HTTPStatusError: if response.status is not a success

        """
        filepath = Path(f"{self.temp_dir}/{photo_reference[:10]}.jpg")
        filepath.touch()
        url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photoreference={photo_reference}&key={env.GMAPS_API_KEY}"
        response = httpx.get(url, follow_redirects=True)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            f.write(response.content)

        return str(filepath)

    def extract_text_from_image(self, image_path: str) -> list[str]:
        """Extract text from an image using EasyOCR"""
        # Read the image
        image = cv2.imread(image_path)

        # Run OCR
        results = self.reader.readtext(image)

        # Extract text from results
        texts = [text for _, text, conf in results if conf > 0.2]
        return texts

    def analyze_place_photos(
        self, photos: list[PlacePhoto], limit: int = 1
    ) -> list[str]:
        all_terms = set()

        # Limit photos to reduce API usage
        for i, photo in enumerate(photos[:limit]):
            if not photo.photo_reference:
                continue

            image_path = self.download_photo(photo.photo_reference)

            # Extract text from image
            texts = self.extract_text_from_image(image_path)

            # Process each text to extract individual terms
            for text in texts:
                # Split text into words
                words = text.split()
                for word in words:
                    # Clean the word (remove punctuation, etc.)
                    clean_word = "".join(
                        c for c in word if c.isalnum() or c.isspace()
                    ).strip()
                    if clean_word and len(clean_word) > 2:  # Ignore very short terms
                        all_terms.add(clean_word.lower())

        return list(all_terms)
