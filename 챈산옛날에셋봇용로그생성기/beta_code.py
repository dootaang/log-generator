import sys
import json
import re
import base64
import struct
import zipfile
import os
import shutil
import markdown
from io import BytesIO
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
                             QCheckBox, QFileDialog, QScrollArea, QLabel, QMessageBox, QColorDialog, 
                             QComboBox, QGroupBox, QFormLayout, QLineEdit)
from PyQt5.QtGui import QFont, QPixmap, QColor
from PyQt5.QtCore import Qt



class CharacterCardReader:

    def __init__(self):

        self.character_data = None

        self.image_data = {}

        self.image_uri_map = {}



    def read_character_card(self, file_path):

        try:

            if file_path.endswith('.png'):

                self.extract_ccv3_from_png(file_path)

            elif file_path.endswith('.json'):

                self.extract_ccv3_from_json(file_path)

            elif file_path.endswith('.charx'):

                self.extract_ccv3_from_charx(file_path)

            else:

                raise ValueError(f"Unsupported file type: {file_path}")

        except Exception as e:

            print(f"Error reading character card: {e}")



    def extract_ccv3_from_png(self, file_path):

        try:

            with open(file_path, 'rb') as f:

                png_signature = f.read(8)

                character_data = None

                

                while True:

                    length_bytes = f.read(4)

                    if len(length_bytes) != 4:

                        break

                    

                    length = struct.unpack('>I', length_bytes)[0]

                    chunk_type = f.read(4).decode('ascii')

                    chunk_data = f.read(length)

                    crc = f.read(4)

                    

                    if chunk_type == 'tEXt':

                        keyword_data, text_data = chunk_data.split(b'\x00', 1)

                        keyword = keyword_data.decode('ascii')

                        

                        if keyword in ['ccv3', 'chara']:

                            try:

                                chara_json_data = base64.b64decode(text_data).decode('utf-8')

                                self.character_data = json.loads(chara_json_data)

                            except (json.JSONDecodeError, base64.binascii.Error) as e:

                                print(f"Failed to decode JSON data for keyword '{keyword}': {e}")

                        else:

                            try:

                                png_data = base64.b64decode(text_data)

                                key = keyword.split('_')[-1]

                                self.image_data[f"chara-ext-asset_{key}.png"] = png_data

                            except (base64.binascii.Error, UnicodeDecodeError) as e:

                                print(f"Failed to decode base64 data for keyword '{keyword}': {e}")



            self.process_asset_data()

        except Exception as e:

            print(f"Error extracting ccv3 from PNG: {e}")



    def extract_ccv3_from_json(self, file_path):

        try:

            with open(file_path, 'r', encoding='utf-8') as f:

                self.character_data = json.load(f)

            self.process_asset_data()

        except Exception as e:

            print(f"Error extracting ccv3 from JSON: {e}")



    def extract_ccv3_from_charx(self, file_path):

        try:

            with zipfile.ZipFile(file_path, 'r') as zip_ref:

                with zip_ref.open('card.json') as json_file:

                    self.character_data = json.load(json_file)

                

                for file_info in zip_ref.infolist():

                    if file_info.filename.startswith('assets/other/'):

                        with zip_ref.open(file_info) as img_file:

                            self.image_data[file_info.filename.split('/')[-1]] = img_file.read()



            self.process_asset_data()

        except Exception as e:

            print(f"Error extracting ccv3 from charx: {e}")



    def process_asset_data(self):

        if not self.character_data:

            return

        spec = self.character_data.get("spec", "")

        if spec == "chara_card_v2":

            self.process_ccv2_assets()

        elif spec == "chara_card_v3":

            self.process_ccv3_assets()



    def process_ccv2_assets(self):

        try:

            extensions = self.character_data.get("data", {}).get("extensions", {})

            risuai = extensions.get("risuai", {})

            additional_assets = risuai.get("additionalAssets", [])



            for asset in additional_assets:

                asset_name, asset_uri, _ = asset

                asset_name = re.sub(r'\.(png|jpg|webp)$', '', asset_name, flags=re.I)

                asset_number = asset_uri.split(':')[1]

                self.image_uri_map[asset_name] = f"chara-ext-asset_{asset_number.strip()}.png"

        except Exception as e:

            print(f"Error processing CCV2 assets: {e}")



    def process_ccv3_assets(self):

        try:

            assets = self.character_data.get("data", {}).get("assets", [])

            for asset in assets:

                asset_name = asset.get("name")

                asset_uri = asset.get("uri")

                asset_number = asset_uri.split(':')[1]

                self.image_uri_map[asset_name] = f"chara-ext-asset_{asset_number.strip()}.png"

        except Exception as e:

            print(f"Error processing CCV3 assets: {e}")



    def get_image_data(self, image_name):

        asset_key = self.image_uri_map.get(image_name.strip())

        if asset_key:

            return self.image_data.get(asset_key)

        return None



class ChatLogPrettifier(QWidget):

    def __init__(self):

        super().__init__()

        self.reader = CharacterCardReader()

        self.assets_folder = 'assets'

        if not os.path.exists(self.assets_folder):

            os.makedirs(self.assets_folder)

        self.asset_name_img_tag_map = {}

        self.colors = {

            'default_bg': '#f0f0f0',

            'default_text': '#000000',

            'user_bg': '#e6f2ff',

            'char_bg': '#fff0e6',

            'single_quotes': '#368d9f',

            'double_quotes': '#ed9213',

            'asterisks': '#ffff00',

            'double_asterisks': '#0766b9',

            'unencapsulated': '#000000'

        }

        self.themes = {

            'Light Pastel': {

                'bg': '#f8f9fa',

                'user_bg': '#e3f2fd',

                'char_bg': '#fff3e0',

                'border': '#d1d9e6'

            },

            'Dark Pastel': {

                'bg': '#2c3e50',

                'user_bg': '#34495e',

                'char_bg': '#2c3e50',

                'border': '#465c71'

            }

        }

        self.current_theme = 'Light Pastel'

        self.custom_regexes = []

        self.initUI()



    def __del__(self):

        shutil.rmtree(self.assets_folder, ignore_errors=True)



    def initUI(self):

        main_layout = QHBoxLayout()

        left_layout = QVBoxLayout()

        right_layout = QVBoxLayout()



        self.input_text = QTextEdit()

        self.input_text.setPlaceholderText("Paste your JSON chat log here or use the 'Upload JSON File' button...")

        left_layout.addWidget(self.input_text)



        self.upload_button = QPushButton('Upload JSON File')

        self.upload_button.clicked.connect(self.upload_json_file)

        left_layout.addWidget(self.upload_button)



        self.upload_char_card_button = QPushButton('Upload Character Card')

        self.upload_char_card_button.clicked.connect(self.upload_char_card)

        left_layout.addWidget(self.upload_char_card_button)



        self.checkbox1 = QCheckBox('오망고/핑퐁')

        self.checkbox2 = QCheckBox('탁구치는 잼민이')

        self.checkbox3 = QCheckBox('클래식 <Thoughts>')

        left_layout.addWidget(self.checkbox1)

        left_layout.addWidget(self.checkbox2)

        left_layout.addWidget(self.checkbox3)



        self.user_label = QLabel('User:')

        self.user_input = QLineEdit('User')

        left_layout.addWidget(self.user_label)

        left_layout.addWidget(self.user_input)



        self.char_label = QLabel('Char:')

        self.char_input = QLineEdit('Char')

        left_layout.addWidget(self.char_label)

        left_layout.addWidget(self.char_input)



        self.add_custom_regex_button = QPushButton('Add Custom Regex')

        self.add_custom_regex_button.clicked.connect(self.add_custom_regex_fields)

        left_layout.addWidget(self.add_custom_regex_button)



        self.convert_button = QPushButton('Convert to HTML')

        self.convert_button.clicked.connect(self.convert_to_html)

        left_layout.addWidget(self.convert_button)



        self.output_text = QTextEdit()

        self.output_text.setReadOnly(True)

        left_layout.addWidget(self.output_text)



        self.img_tags_from_arcalive = QTextEdit()

        self.img_tags_from_arcalive.setPlaceholderText("Paste your <img> tags here after uploading images to arca.live or anything equivalent...")

        left_layout.addWidget(self.img_tags_from_arcalive)



        # Asset preview area

        self.asset_preview = QScrollArea()

        self.asset_preview.setWidgetResizable(True)

        self.asset_preview_content = QWidget()

        self.asset_preview_layout = QVBoxLayout(self.asset_preview_content)

        self.asset_preview.setWidget(self.asset_preview_content)

        right_layout.addWidget(QLabel("Asset Preview:"))

        right_layout.addWidget(self.asset_preview)



        # Add color selection group

        color_group = QGroupBox("Text Colors")

        color_layout = QFormLayout()

        self.color_buttons = {}

        for key in self.colors.keys():

            if key not in ['default_bg', 'default_text', 'user_bg', 'char_bg']:

                button = QPushButton()

                button.setStyleSheet(f"background-color: {self.colors[key]};")

                button.clicked.connect(lambda _, k=key: self.choose_color(k))

                self.color_buttons[key] = button

                color_layout.addRow(key.replace('_', ' ').title(), button)

        color_group.setLayout(color_layout)

        left_layout.addWidget(color_group)



        # Add theme selection

        theme_layout = QHBoxLayout()

        theme_layout.addWidget(QLabel("Theme:"))

        self.theme_combo = QComboBox()

        self.theme_combo.addItems(self.themes.keys())

        self.theme_combo.currentTextChanged.connect(self.change_theme)

        theme_layout.addWidget(self.theme_combo)

        left_layout.addLayout(theme_layout)



        main_layout.addLayout(left_layout, 2)

        main_layout.addLayout(right_layout, 1)



        self.setLayout(main_layout)

        self.setGeometry(300, 300, 800, 600)

        self.setWindowTitle('Chat Log Prettifier')

        self.show()



    def upload_json_file(self):

        options = QFileDialog.Options()

        file_name, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json);;All Files (*)", options=options)

        if file_name:

            try:

                with open(file_name, 'r', encoding='utf-8') as file:

                    json_data = file.read()

                    self.input_text.setPlainText(json_data)

            except Exception as e:

                self.output_text.setPlainText(f"Error: {str(e)}")



    def upload_char_card(self):

        options = QFileDialog.Options()

        file_name, _ = QFileDialog.getOpenFileName(self, "Open Character Card", "", "Character Card Files (*.json *.png *.charx);;All Files (*)", options=options)

        if file_name:

            try:

                self.reader.read_character_card(file_name)

                self.output_text.setPlainText("Character card loaded successfully.")

                self.update_asset_preview()

                self.save_images_to_disk()

            except Exception as e:

                self.output_text.setPlainText(f"Error: {str(e)}")



    def update_asset_preview(self):

        # Clear existing content

        for i in reversed(range(self.asset_preview_layout.count())): 

            self.asset_preview_layout.itemAt(i).widget().setParent(None)



        # Add new content

        for asset_name, asset_data in self.reader.image_data.items():

            label = QLabel(asset_name)

            pixmap = QPixmap()

            pixmap.loadFromData(asset_data)

            label.setPixmap(pixmap.scaledToWidth(200, Qt.SmoothTransformation))

            self.asset_preview_layout.addWidget(label)



    def choose_color(self, key):

        color = QColorDialog.getColor()

        if color.isValid():

            self.colors[key] = color.name()

            self.color_buttons[key].setStyleSheet(f"background-color: {color.name()};")



    def change_theme(self, theme_name):

        self.current_theme = theme_name

        # Update color buttons to reflect theme colors

        for key, button in self.color_buttons.items():

            if key in self.themes[theme_name]:

                self.colors[key] = self.themes[theme_name][key]

                button.setStyleSheet(f"background-color: {self.colors[key]};")



    def add_custom_regex_fields(self):

        # Add input and output fields for custom regex

        regex_input = QLineEdit()

        regex_input.setPlaceholderText("Enter custom regex")

        regex_output = QLineEdit()

        regex_output.setPlaceholderText("Enter replacement string")

        self.custom_regexes.append((regex_input, regex_output))

        

        self.layout().addWidget(regex_input)

        self.layout().addWidget(regex_output)



    def convert_to_html(self):

        try:

            json_data = json.loads(self.input_text.toPlainText())

            messages = json_data['data']['message']

            html_content = self.generate_html(messages)

            

            # Create the asset_name_img_tag_map

            img_tags = self.img_tags_from_arcalive.toPlainText()

            self.create_asset_name_img_tag_map(img_tags)

            

            # Replace image tags in the HTML content

            html_with_images = self.replace_image_tags(html_content)

            

            self.output_text.setPlainText(html_with_images)

        except Exception as e:

            self.output_text.setPlainText(f"Error: {str(e)}")



    def generate_html(self, messages):

        theme = self.themes[self.current_theme]

        user_name = self.user_input.text()

        char_name = self.char_input.text()

        html = f'<div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; background-color: {theme["bg"]};">'

        

        for message in messages:

            role = message.get('role', 'unknown')

            content = message.get('data', '')

            

            # Apply custom regexes

            content = self.apply_custom_regexes(content)

            

            if self.checkbox1.isChecked():

                content = self.apply_regex_omango_pingpong(content)

            if self.checkbox2.isChecked():

                content = self.apply_regex_pingpong_kid(content)

            if self.checkbox3.isChecked():

                content = self.apply_regex_classic_thoughts(content)

            

            # Preserve image tags before converting markdown

            content = self.preserve_image_tags(content)

            

            # Convert markdown to HTML

            content = markdown.markdown(content)

            

            # Apply color styling

            content = self.apply_color_styling(content)

            

            bg_color = theme['user_bg'] if role == 'user' else theme['char_bg']

            display_name = user_name if role == 'user' else char_name

            html += f'<div style="padding: 10px; border-radius: 10px; margin: 5px 0; border: 1px solid {theme["border"]}; background-color: {bg_color};">'

            html += f'<strong>{display_name.capitalize()}:</strong> {content}'

            html += '</div>'

        

        html += '</div>'

        return html



    def preserve_image_tags(self, content):

        # Replace image tags with placeholders

        img_tag_pattern = re.compile(r'<img="([^"]+)">')

        placeholders = []

        index = 0

        def replace_img_tag(match):

            nonlocal index

            placeholder = f"IMG_TAG_PLACEHOLDER_{index}"

            placeholders.append((placeholder, match.group(0)))

            index += 1

            return placeholder

        

        content = img_tag_pattern.sub(replace_img_tag, content)

        self.img_tag_placeholders = placeholders

        return content



    def restore_image_tags(self, content):

        # Replace placeholders with original image tags

        for placeholder, img_tag in self.img_tag_placeholders:

            content = content.replace(placeholder, img_tag)

        return content



    def apply_custom_regexes(self, content):

        for regex_input, regex_output in self.custom_regexes:

            pattern = regex_input.text()

            replacement = regex_output.text()

            if pattern:

                content = re.sub(pattern, replacement, content)

        return content



    def apply_color_styling(self, content):

        def style_text(match, color, additional_style=""):

            text = match.group(1)

            # Ensure we don't wrap existing spans

            if text.startswith('<span') and text.endswith('</span>'):

                return match.group(0)

            return f'<span style="color: {color};{additional_style}">{match.group(0)}</span>'  # Preserve the quotes



        # Apply color styling to different text encapsulations

        patterns = [

            (r"(?<!\w)'([^']*?)'(?!\w)", self.colors["single_quotes"]),  # Single quotes

            (r'(?<!\w)"([^"]*?)"(?!\w)', self.colors["double_quotes"]),  # Double quotes

            (r'\*(.*?)\*', self.colors["asterisks"], " font-style: italic;"),  # Single asterisks

            (r'\*\*(.*?)\*\*', self.colors["double_asterisks"], " font-weight: bold;"),  # Double asterisks

        ]



        for pattern, color, *additional in patterns:

            content = re.sub(pattern, lambda m: style_text(m, color, additional[0] if additional else ""), content)



        content = content.replace('\n', '<br>')  # Convert newlines to <br> tags

        content = self.restore_image_tags(content)  # Restore image tags

        return content



    def create_asset_name_img_tag_map(self, img_tags):

        self.asset_name_img_tag_map = {}

        img_tag_pattern = re.compile(r'<img[^>]+src="([^"]+)"[^>]*>')

        

        # Get the list of files in the assets folder (without extensions)

        asset_files = [os.path.splitext(f)[0] for f in os.listdir(self.assets_folder) 

                       if f.lower().endswith(('.png', '.jpg', '.webp'))]

        

        for asset_name in asset_files:

            match = img_tag_pattern.search(img_tags)

            if match:

                self.asset_name_img_tag_map[asset_name] = match.group(0)

                img_tags = img_tags[match.end():]

            else:

                break



    def replace_image_tags(self, html_content):

        print(self.asset_name_img_tag_map.keys())

        def replace_func(match):

            image_name = match.group(1).strip()

            return self.asset_name_img_tag_map.get(image_name, match.group(0))



        # Replace <img="..."> tags

        html_content = re.sub(r'<img="([^"]+)">', replace_func, html_content)

        

        # Replace {{img::...}} tags (note the double colon)

        html_content = re.sub(r'{{img::([^}]+)}}', replace_func, html_content)

        

        return html_content



    def save_images_to_disk(self):

        for image_name, image_data in self.reader.image_data.items():

            asset_name = next((key for key, value in self.reader.image_uri_map.items() if value == image_name), image_name)

            file_path = os.path.join(self.assets_folder, f"{asset_name}.png")

            with open(file_path, 'wb') as img_file:

                img_file.write(image_data)

        self.open_assets_folder()

    def open_assets_folder(self):

        if sys.platform == 'win32':

            os.startfile(self.assets_folder)

        elif sys.platform == 'darwin':

            os.system(f'open {self.assets_folder}')

        else:

            os.system(f'xdg-open {self.assets_folder}')



    def apply_regex_omango_pingpong(self, text):

        match = re.search(r'## Response[\n]*(.*)', text, re.DOTALL)

        return match.group(1) if match else text



    def apply_regex_pingpong_kid(self, text):

        match = re.search(r'AI 응답[\n]*(.*)', text, re.DOTALL)

        return match.group(1) if match else text



    def apply_regex_classic_thoughts(self, text):

        match = re.search(r'</Thoughts>(.*)', text, re.DOTALL)

        return match.group(1) if match else text



    def closeEvent(self, event):

        shutil.rmtree(self.assets_folder, ignore_errors=True)

        event.accept()



if __name__ == '__main__':

    app = QApplication(sys.argv)

    ex = ChatLogPrettifier()

    sys.exit(app.exec_())