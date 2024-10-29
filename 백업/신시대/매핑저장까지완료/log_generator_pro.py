import re
import os
import sys
import contextlib
import json
import os
import base64
import struct
import zipfile
import shutil
import os
import sys
import glob
from PyQt6.QtWidgets import QFileDialog
from io import BytesIO
from datetime import datetime  # 날짜/시간 처리용
from PyQt6.QtCore import QTimer  # 타이머 기능용
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTextEdit, QLabel, QPushButton,
                           QColorDialog, QLineEdit, QCheckBox, QSpinBox,
                           QTabWidget, QScrollArea, QComboBox, QFrame,
                           QGridLayout, QFileDialog, QSplitter)
from PyQt6.QtGui import QFont, QClipboard, QColor, QPalette, QIcon
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QTabWidget
from PyQt6.QtWidgets import (QInputDialog, QMessageBox, QMenu)
from PyQt6.QtCore import QStandardPaths
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtWidgets import QSlider


class ImageCache:
    def __init__(self):
        self.cache_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation)
        self.mapping_file = os.path.join(self.cache_path, 'image_mappings.json')
        self.mappings = {}
        self.load_mappings()

    def load_mappings(self):
        try:
            if os.path.exists(self.mapping_file):
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    self.mappings = json.load(f)
        except Exception as e:
            print(f"매핑 로드 실패: {e}")
            self.mappings = {}

    def save_mappings(self):
        try:
            os.makedirs(self.cache_path, exist_ok=True)
            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                json.dump(self.mappings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"매핑 저장 실패: {e}")

class MappingManager:
    def __init__(self, parent):
        self.parent = parent
        self.mappings_file = os.path.join(
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation),
            'image_mappings'
        )
        os.makedirs(os.path.dirname(self.mappings_file), exist_ok=True)

    def save_mapping_set(self, name):
        """현재 매핑 세트를 저장"""
        try:
            # 매핑 데이터 수집
            mappings = []
            for entry in self.parent.image_url_container.findChildren(ImageUrlEntry):
                tag = entry.tag_input.text().strip()
                url = entry.url_input.text().strip()
                if tag and url:  # 태그와 URL이 모두 있는 경우만 저장
                    mappings.append({
                        'tag': tag,
                        'url': url
                    })

            if not mappings:
                raise ValueError("저장할 매핑이 없습니다.")

            # 매핑 세트 저장
            file_path = f"{self.mappings_file}_{name}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(mappings, f, ensure_ascii=False, indent=2)

            return True, f"매핑 세트 '{name}'이(가) 저장되었습니다."
            
        except Exception as e:
            return False, f"매핑 저장 중 오류 발생: {str(e)}"

    def load_mapping_set(self, name):
        """저장된 매핑 세트 불러오기"""
        try:
            file_path = f"{self.mappings_file}_{name}.json"
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"매핑 파일을 찾을 수 없습니다: {name}")

            with open(file_path, 'r', encoding='utf-8') as f:
                mappings = json.load(f)

            # 기존 매핑 제거
            for widget in self.parent.image_url_container.findChildren(ImageUrlEntry):
                widget.deleteLater()

            # 새 매핑 추가
            for mapping in mappings:
                entry = ImageUrlEntry(self.parent.image_url_container)
                entry.from_dict(mapping)
                self.parent.image_url_layout.addWidget(entry)

            return True, f"매핑 세트 '{name}'을(를) 불러왔습니다."
        except Exception as e:
            return False, f"매핑 불러오기 중 오류 발생: {str(e)}"

    def delete_mapping_set(self, name):
        """저장된 매핑 세트 삭제"""
        try:
            file_path = f"{self.mappings_file}_{name}.json"
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"매핑 파일을 찾을 수 없습니다: {name}")

            os.remove(file_path)
            return True, f"매핑 세트 '{name}'이(가) 삭제되었습니다."
        except Exception as e:
            return False, f"매핑 삭제 중 오류 발생: {str(e)}"

    def get_available_mapping_sets(self):
        """저장된 매핑 세트 목록 반환"""
        try:
            mapping_files = glob.glob(f"{self.mappings_file}_*.json")
            return [os.path.basename(f)[len(os.path.basename(self.mappings_file)) + 1:-5] 
                   for f in mapping_files]
        except Exception:
            return []
    
    def save_mapping_set_dialog(self):
        """매핑 세트 저장 다이얼로그"""
        name, ok = QInputDialog.getText(
            self.parent,
            '매핑 세트 저장',
            '저장할 매핑 세트의 이름을 입력하세요:'
        )
        
        if ok and name:
            success, message = self.save_mapping_set(name)
            QMessageBox.information(self.parent, "매핑 저장", message)

    def load_mapping_set_dialog(self):
        """매핑 세트 불러오기 다이얼로그"""
        available_sets = self.get_available_mapping_sets()
        if not available_sets:
            QMessageBox.information(self.parent, "매핑 불러오기", "저장된 매핑 세트가 없습니다.")
            return
        
        name, ok = QInputDialog.getItem(
            self.parent,
            "매핑 불러오기",
            "불러올 매핑 세트를 선택하세요:",
            available_sets,
            0,
            False
        )
        
        if ok and name:
            success, message = self.load_mapping_set(name)
            QMessageBox.information(self.parent, "매핑 불러오기", message)

    def delete_mapping_set_dialog(self):
        """매핑 세트 삭제 다이얼로그"""
        available_sets = self.get_available_mapping_sets()
        if not available_sets:
            QMessageBox.information(self.parent, "매핑 삭제", "저장된 매핑 세트가 없습니다.")
            return
        
        name, ok = QInputDialog.getItem(
            self.parent,
            "매핑 삭제",
            "삭제할 매핑 세트를 선택하세요:",
            available_sets,
            0,
            False
        )
        
        if ok and name:
            reply = QMessageBox.question(
                self.parent,
                "매핑 삭제 확인",
                f"매핑 세트 '{name}'을(를) 정말 삭제하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                success, message = self.delete_mapping_set(name)
                QMessageBox.information(self.parent, "매핑 삭제", message)


class CharacterCardHandler:
    def __init__(self):
        self.character_data = None
        self.image_data = {}
        self.image_uri_map = {}
        self.assets_folder = os.path.join(
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation),
            'temp_assets'
        )
        
        # 임시 폴더 생성
        os.makedirs(self.assets_folder, exist_ok=True)

    def read_character_card(self, file_path):
        """캐릭터 카드 파일 읽기"""
        try:
            if file_path.endswith('.png'):
                self._extract_from_png(file_path)
            elif file_path.endswith('.json'):
                self._extract_from_json(file_path)
            elif file_path.endswith('.charx'):
                self._extract_from_charx(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_path}")
            
            return True
        except Exception as e:
            print(f"Error reading character card: {e}")
            return False

    def _extract_from_png(self, file_path):
        """PNG 파일에서 데이터 추출"""
        try:
            with open(file_path, 'rb') as f:
                png_signature = f.read(8)
                while True:
                    try:
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
                                    print(f"Character data loaded: {keyword}")
                                except Exception as e:
                                    print(f"Error decoding character data: {e}")
                            else:
                                try:
                                    if '_' in keyword:  # 이미지 데이터를 포함하는 키워드인지 확인
                                        asset_id = keyword.split(':')[-1] if ':' in keyword else '0'
                                        img_key = f"chara-ext-asset_:{asset_id}"
                                        png_data = base64.b64decode(text_data)
                                        self.image_data[img_key] = png_data
                                        print(f"Image data loaded: {img_key}, size: {len(png_data)} bytes")
                                except Exception as e:
                                    print(f"Error processing image data for {keyword}: {e}")
                    except Exception as e:
                        print(f"Error processing PNG chunk: {e}")
                        break
        
            # 데이터 처리 결과 출력
            print(f"Total images found: {len(self.image_data)}")
            self._process_assets()
            return True
        except Exception as e:
            print(f"Error reading PNG file: {e}")
            return False

    def _extract_from_json(self, file_path):
        """JSON 파일에서 데이터 추출"""
        with open(file_path, 'r', encoding='utf-8') as f:
            self.character_data = json.load(f)
        self._process_assets()

    def _extract_from_charx(self, file_path):
        """CHARX 파일에서 데이터 추출"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # 캐릭터 카드 데이터 로드
                with zip_ref.open('card.json') as json_file:
                    self.character_data = json.load(json_file)
                
                # 에셋 정보 미리 수집
                assets = self.character_data.get("data", {}).get("assets", [])
                asset_names = {str(i): asset.get("name", f"asset_{i}") 
                            for i, asset in enumerate(assets)}
                
                print(f"\nFound asset mappings in card.json:")
                for idx, name in asset_names.items():
                    print(f"Asset {idx} -> {name}")
                
                # 에셋 파일 처리
                asset_count = 0
                for file_info in zip_ref.infolist():
                    if file_info.filename.startswith('assets/'):
                        try:
                            # 파일 번호 추출 (예: assets/other/0.png -> 0)
                            asset_num = os.path.splitext(os.path.basename(file_info.filename))[0]
                            
                            # card.json의 에셋 이름 사용
                            asset_name = asset_names.get(asset_num, f"asset_{asset_num}")
                            print(f"Processing asset file {file_info.filename} -> {asset_name}")
                            
                            # 이미지 데이터 읽기
                            with zip_ref.open(file_info) as img_file:
                                image_data = img_file.read()
                                # 키 형식을 PNG 파일과 동일하게 맞춤
                                key = f"chara-ext-asset_:{asset_name}"
                                self.image_data[key] = image_data
                                
                                # 이미지 URI 매핑 생성
                                self.image_uri_map[asset_name] = key
                                asset_count += 1
                        except Exception as e:
                            print(f"Error processing asset {file_info.filename}: {e}")
                            continue
                
                print(f"\nExtracted from CHARX:")
                print(f"Total assets found: {asset_count}")
                print(f"Image mappings created: {len(self.image_uri_map)}")
                
                # 디버그 정보 출력
                self.debug_print_asset_info()
                
                return True
        except Exception as e:
            print(f"Error extracting from CHARX: {e}")
            return False

    def _process_assets(self):
        """에셋 데이터 처리"""
        if not self.character_data:
            return
            
        spec = self.character_data.get("spec", "")
        if spec == "chara_card_v2":
            self._process_ccv2_assets()
        elif spec == "chara_card_v3":
            self._process_ccv3_assets()

    def _process_ccv2_assets(self):
        """CCv2 에셋 처리"""
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
            print(f"Error processing CCv2 assets: {e}")

    # CharacterCardHandler 클래스의 _process_ccv3_assets 메서드를 수정합니다
    def _process_ccv3_assets(self):
        """CCv3 에셋 처리"""
        try:
            print("\nProcessing CCv3 assets...")
            assets = self.character_data.get("data", {}).get("assets", [])
            print(f"Found {len(assets)} assets in character data")
            
            # .charx 파일에서 로드된 경우 이미 매핑이 되어 있으므로 건너뜀
            if not self.image_uri_map:
                for i, asset in enumerate(assets):
                    try:
                        asset_name = asset.get("name", "").strip()
                        if not asset_name:  # 이름이 없는 경우 번호 사용
                            asset_name = f"asset_{i}"
                        
                        # 여기가 핵심 수정 부분: 이미지 데이터의 키를 인덱스로 찾음
                        image_key = f"chara-ext-asset_:{i}"
                        
                        if image_key in self.image_data:
                            # asset_name(원본 태그명)을 키로 사용하여 매핑
                            self.image_uri_map[asset_name] = image_key
                            print(f"Successfully mapped: {asset_name} -> {image_key}")
                        else:
                            print(f"Warning: No image data found for {image_key}")
                            
                    except Exception as e:
                        print(f"Error processing individual asset {i}: {e}")
                        continue
                
                print(f"\nProcessing completed:")
                print(f"Total assets found: {len(assets)}")
                print(f"Successfully mapped: {len(self.image_uri_map)} assets")
                
            # 디버그 정보 출력
            self.debug_print_asset_info()
            
        except Exception as e:
            print(f"Error in _process_ccv3_assets: {e}")

    def save_assets(self):
        """에셋을 임시 폴더에 저장"""
        try:
            saved_count = 0
            print("\nSaving assets...")
            print(f"Image URI map contains {len(self.image_uri_map)} entries")
            print(f"Image data contains {len(self.image_data)} entries")
            
            # 디버깅을 위한 키 출력
            print("\nAvailable image_data keys:")
            for key in self.image_data.keys():
                print(f"- {key}")
                
            print("\nImage URI map entries:")
            for name, key in self.image_uri_map.items():
                print(f"- {name} -> {key}")
            
            for asset_name, asset_key in self.image_uri_map.items():
                try:
                    # 이미지 데이터가 있는지 확인
                    image_data = self.image_data.get(asset_key)
                    if image_data:
                        file_path = os.path.join(self.assets_folder, f"{asset_name}.png")
                        with open(file_path, 'wb') as img_file:
                            img_file.write(image_data)
                        saved_count += 1
                        print(f"Saved asset: {asset_name}")
                    else:
                        print(f"Warning: No image data found for {asset_key}")
                except Exception as e:
                    print(f"Error saving asset {asset_name}: {e}")
            
            print(f"\nSuccessfully saved {saved_count} assets")
            return saved_count > 0
        except Exception as e:
            print(f"Error in save_assets: {e}")
            return False

    def _extract_from_png(self, file_path):
        """PNG 파일에서 데이터 추출"""
        try:
            with open(file_path, 'rb') as f:
                png_signature = f.read(8)
                while True:
                    try:
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
                                    print(f"Character data loaded: {keyword}")
                                    # CCv3 데이터를 로드한 직후 바로 처리
                                    if keyword == 'ccv3':
                                        self._process_ccv3_assets()
                                except Exception as e:
                                    print(f"Error decoding character data: {e}")
                            else:
                                try:
                                    png_data = base64.b64decode(text_data)
                                    key = f"chara-ext-asset_:{keyword.split(':')[-1]}"
                                    self.image_data[key] = png_data
                                    print(f"Image data loaded: {key}, size: {len(png_data)} bytes")
                                except Exception as e:
                                    print(f"Error processing image data for {keyword}: {e}")
                    except Exception as e:
                        print(f"Error processing PNG chunk: {e}")
                        break
            
            print(f"\nExtraction completed:")
            print(f"Total images found: {len(self.image_data)}")
            print(f"Total mappings created: {len(self.image_uri_map)}")
            return True
        except Exception as e:
            print(f"Error reading PNG file: {e}")
            return False

    def cleanup(self):
        """임시 파일 정리"""
        try:
            shutil.rmtree(self.assets_folder, ignore_errors=True)
        except Exception as e:
            print(f"Error cleaning up assets: {e}")

    def debug_print_asset_info(self):
            """에셋 정보 출력 (디버깅용)"""
            print("\n=== Asset Debug Information ===")
            print(f"Total image data entries: {len(self.image_data)}")
            print("\nImage data keys:")
            for key in self.image_data.keys():
                print(f"- {key}")
            
            print("\nImage URI mappings:")
            for name, uri in self.image_uri_map.items():
                print(f"- {name} -> {uri}")
            
            print("\nCharacter data assets:")
            assets = self.character_data.get("data", {}).get("assets", [])
            for asset in assets:
                print(f"- Name: {asset.get('name')}, URI: {asset.get('uri')}")
            print("============================\n")

class RGBColorSlider(QWidget):
    """RGB 슬라이더 방식의 색상 선택 컴포넌트"""
    colorChanged = pyqtSignal(str)  # 색상 변경 시그널

    def __init__(self, initial_color="#000000", parent=None):
        super().__init__(parent)
        self.setMinimumWidth(200)
        self.init_ui(initial_color)

    def init_ui(self, initial_color):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # RGB 값 초기화
        color = QColor(initial_color)
        self.r, self.g, self.b = color.red(), color.green(), color.blue()

        # 색상 미리보기
        preview_layout = QHBoxLayout()
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(50, 50)
        self.update_preview()
        preview_layout.addWidget(self.color_preview)
        preview_layout.addStretch()
        layout.addLayout(preview_layout)

        # RGB 슬라이더 생성
        self.sliders = {}
        self.labels = {}
        self.spinboxes = {}
        
        for color, initial_value in [('R', self.r), ('G', self.g), ('B', self.b)]:
            slider_layout = QHBoxLayout()
            
            # 레이블
            label = QLabel(color)
            label.setFixedWidth(20)
            slider_layout.addWidget(label)
            
            # 슬라이더
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 255)
            slider.setValue(initial_value)
            slider.setStyleSheet(f"""
                QSlider::groove:horizontal {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 black, stop:1 {color.lower()});
                    height: 8px;
                    border-radius: 4px;
                }}
                QSlider::handle:horizontal {{
                    background: white;
                    border: 2px solid #ccc;
                    width: 16px;
                    height: 16px;
                    margin: -5px 0;
                    border-radius: 9px;
                }}
            """)
            slider.valueChanged.connect(lambda v, c=color: self.update_color(c, v))
            slider_layout.addWidget(slider)
            
            # 스핀박스
            spinbox = QSpinBox()
            spinbox.setRange(0, 255)
            spinbox.setValue(initial_value)
            spinbox.valueChanged.connect(lambda v, c=color: self.update_color(c, v))
            spinbox.setFixedWidth(70)
            slider_layout.addWidget(spinbox)
            
            self.sliders[color] = slider
            self.labels[color] = label
            self.spinboxes[color] = spinbox
            
            layout.addLayout(slider_layout)

        # 16진수 색상 코드 표시
        hex_layout = QHBoxLayout()
        hex_layout.addWidget(QLabel("Hex:"))
        self.hex_value = QLineEdit()
        self.hex_value.setText(initial_color)
        self.hex_value.setFixedWidth(100)
        self.hex_value.editingFinished.connect(self.hex_color_changed)
        hex_layout.addWidget(self.hex_value)
        hex_layout.addStretch()
        layout.addLayout(hex_layout)

    def update_color(self, color, value):
        """색상값 업데이트"""
        # 슬라이더와 스핀박스 동기화
        self.sliders[color].setValue(value)
        self.spinboxes[color].setValue(value)
        
        # RGB 값 저장
        if color == 'R':
            self.r = value
        elif color == 'G':
            self.g = value
        else:
            self.b = value
            
        self.update_preview()
        self.update_hex_value()
        
        # 색상 변경 시그널 발생
        hex_color = f"#{self.r:02x}{self.g:02x}{self.b:02x}"
        self.colorChanged.emit(hex_color)

    def update_preview(self):
        """색상 미리보기 업데이트 - RGB 슬라이더용"""
        style = f"""
            QLabel {{
                background-color: rgb({self.r}, {self.g}, {self.b});
                border: 1px solid #ccc;
                border-radius: 4px;
            }}
        """
        self.color_preview.setStyleSheet(style)

    def update_color(self, color, value):
        """색상값 업데이트"""
        # 슬라이더와 스핀박스 동기화
        self.sliders[color].setValue(value)
        self.spinboxes[color].setValue(value)
        
        # RGB 값 저장
        if color == 'R':
            self.r = value
        elif color == 'G':
            self.g = value
        else:
            self.b = value
            
        self.update_preview()  # 실제 컬러 프리뷰 업데이트
        self.update_hex_value()
        
        # 색상 변경 시그널 발생
        hex_color = f"#{self.r:02x}{self.g:02x}{self.b:02x}"
        self.colorChanged.emit(hex_color)

    def update_hex_value(self):
        """16진수 색상 코드 업데이트"""
        hex_color = f"#{self.r:02x}{self.g:02x}{self.b:02x}"
        self.hex_value.setText(hex_color)

    def hex_color_changed(self):
        """16진수 색상 코드 입력 시 처리"""
        try:
            hex_color = self.hex_value.text().strip('#')
            if len(hex_color) == 6:
                self.r = int(hex_color[:2], 16)
                self.g = int(hex_color[2:4], 16)
                self.b = int(hex_color[4:], 16)
                
                # 슬라이더와 스핀박스 업데이트
                for color, value in [('R', self.r), ('G', self.g), ('B', self.b)]:
                    self.sliders[color].setValue(value)
                    self.spinboxes[color].setValue(value)
                
                self.update_preview()
                self.colorChanged.emit(f"#{hex_color}")
        except ValueError:
            # 잘못된 입력 시 이전 값으로 복원
            self.update_hex_value()

    def get_color(self):
        """현재 선택된 색상 반환"""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def setColor(self, color):
        """색상 설정"""
        try:
            qcolor = QColor(color)
            self.r = qcolor.red()
            self.g = qcolor.green()
            self.b = qcolor.blue()
            
            # UI 업데이트
            for color, value in [('R', self.r), ('G', self.g), ('B', self.b)]:
                self.sliders[color].setValue(value)
                self.spinboxes[color].setValue(value)
            
            self.update_preview()
            self.update_hex_value()
        except Exception as e:
            print(f"Error setting color: {str(e)}")

    def reset_to_default(self):
        """기본 색상으로 리셋"""
        self.setColor("#000000")  # 검은색으로 초기화
        self.colorChanged.emit("#000000")

    def get_brightness(self):
        """색상의 밝기 계산 (0~255)"""
        return (self.r * 299 + self.g * 587 + self.b * 114) / 1000

    # 추가: 밝기에 따라 텍스트 색상 결정
    def get_text_color(self):
        """배경색 밝기에 따라 텍스트 색상 반환"""
        brightness = self.get_brightness()
        return "#000000" if brightness > 128 else "#ffffff"
            

class EnhancedColorDialog(QDialog):
    """향상된 색상 선택 다이얼로그"""
    def __init__(self, initial_color="#000000", parent=None):
        super().__init__(parent)
        self.selected_color = initial_color
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("색상 선택")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # 탭 위젯 생성
        tab_widget = QTabWidget()
        
        # 기본 색상 선택기 탭
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        self.color_dialog = QColorDialog()
        self.color_dialog.setOptions(
            QColorDialog.ColorDialogOption.DontUseNativeDialog |
            QColorDialog.ColorDialogOption.ShowAlphaChannel
        )
        self.color_dialog.currentColorChanged.connect(self.on_basic_color_changed)
        basic_layout.addWidget(self.color_dialog)
        tab_widget.addTab(basic_tab, "기본 선택기")
        
        # RGB 슬라이더 탭
        rgb_tab = QWidget()
        rgb_layout = QVBoxLayout(rgb_tab)
        self.rgb_slider = RGBColorSlider(initial_color=self.selected_color)
        self.rgb_slider.colorChanged.connect(self.on_rgb_color_changed)
        rgb_layout.addWidget(self.rgb_slider)
        tab_widget.addTab(rgb_tab, "RGB 슬라이더")
        
        layout.addWidget(tab_widget)
        
        # 확인/취소 버튼
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def on_basic_color_changed(self, color):
        """기본 색상 선택기에서 색상이 변경될 때"""
        self.selected_color = color.name()
        self.rgb_slider.setColor(self.selected_color)

    def on_rgb_color_changed(self, color):
        """RGB 슬라이더에서 색상이 변경될 때"""
        self.selected_color = color
        self.color_dialog.setCurrentColor(QColor(color))

    def get_selected_color(self):
        """선택된 색상 반환"""
        return self.selected_color

    @staticmethod
    def getColor(initial_color="#000000", parent=None):
        """정적 메서드로 색상 선택 다이얼로그 실행"""
        dialog = EnhancedColorDialog(initial_color, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_selected_color(), True
        return initial_color, False

class PresetManager:
    def __init__(self, main_window):
        self.main_window = main_window
        # 프리셋 파일 경로 설정
        self.presets_file = os.path.join(
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation),
            'presets.json'
        )
        # 디렉토리 생성
        os.makedirs(os.path.dirname(self.presets_file), exist_ok=True)
        self.presets = {}  # 프리셋 데이터 초기화
        self.load_presets()  # 저장된 프리셋 로드

    def load_presets(self):
        """저장된 프리셋 불러오기"""
        try:
            if os.path.exists(self.presets_file):
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    self.presets = json.load(f)
        except Exception as e:
            print(f"프리셋 로드 중 오류 발생: {e}")
            self.presets = {}

    def save_presets(self):
        """프리셋을 파일에 저장"""
        try:
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(self.presets, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(
                self.main_window,
                '오류',
                f'프리셋 저장 중 오류가 발생했습니다: {str(e)}'
            )

    def save_current_settings(self):
        """현재 설정을 프리셋으로 저장"""
        name, ok = QInputDialog.getText(
            self.main_window,
            '프리셋 저장',
            '프리셋 이름을 입력하세요:'
        )
        
        if ok and name:
            if name in self.presets:
                reply = QMessageBox.question(
                    self.main_window,
                    '프리셋 덮어쓰기',
                    f'"{name}" 프리셋이 이미 존재합니다. 덮어쓰시겠습니까?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            try:
                settings = {
                    'template': {
                        'show_inner_box': self.main_window.show_inner_box.isChecked(),
                        'outer_box_color': self.main_window.outer_box_color.get_color(),
                        'inner_box_color': self.main_window.inner_box_color.get_color(),
                        'shadow_intensity': self.main_window.shadow_intensity.value()
                    },
                    'profile': {
                        'show_profile': self.main_window.show_profile.isChecked(),
                        'show_profile_image': self.main_window.show_profile_image.isChecked(),
                        'show_bot_name': self.main_window.show_bot_name.isChecked(),
                        'show_tags': self.main_window.show_tags.isChecked(),
                        'show_divider': self.main_window.show_divider.isChecked(),
                        'frame_style': self.main_window.frame_style.currentText(),
                        'width': self.main_window.width_input.value(),
                        'height': self.main_window.height_input.value(),
                        'image_url': self.main_window.image_url.text(),
                        'profile_border_color': self.main_window.profile_border_color.get_color()
                    },
                    'bot': {
                        'name': self.main_window.bot_name.text(),
                        'name_color': self.main_window.bot_name_color.get_color()
                    },
                    'tags': [
                        {
                            'text': box.text(),
                            'color': self.main_window.tag_colors[i].get_color()
                        }
                        for i, box in enumerate(self.main_window.tag_boxes)
                    ],
                    'divider': {
                        'style': self.main_window.divider_style.currentText(),
                        'thickness': self.main_window.divider_thickness.value(),
                        'outer_color': self.main_window.divider_outer_color.get_color(),
                        'inner_color': self.main_window.divider_inner_color.get_color(),
                        'solid_color': self.main_window.divider_solid_color.get_color()
                    },
                    'text': {
                        'indent': self.main_window.text_indent.value(),
                        'dialog_color': self.main_window.dialog_color.get_color(),
                        'narration_color': self.main_window.narration_color.get_color(),
                        'dialog_bold': self.main_window.dialog_bold.isChecked(),
                        'remove_asterisk': self.main_window.remove_asterisk.isChecked(),
                        'convert_ellipsis': self.main_window.convert_ellipsis.isChecked()
                    },
                    'word_replace': [
                        {
                            'from': entry.from_word.text(),
                            'to': entry.to_word.text()
                        }
                        for entry in self.main_window.word_replace_container.findChildren(WordReplaceEntry)
                    ]
                }

                self.presets[name] = settings
                self.save_presets()
                QMessageBox.information(
                    self.main_window,
                    '저장 완료',
                    f'프리셋 "{name}"이(가) 저장되었습니다.'
                )

            except Exception as e:
                QMessageBox.warning(
                    self.main_window,
                    '오류',
                    f'프리셋 저장 중 오류가 발생했습니다: {str(e)}'
                )

    def delete_preset(self, name):
        """프리셋 삭제"""
        try:
            if name in self.presets:
                reply = QMessageBox.question(
                    self.main_window,
                    '프리셋 삭제',
                    f'"{name}" 프리셋을 삭제하시겠습니까?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    del self.presets[name]
                    self.save_presets()
                    QMessageBox.information(
                        self.main_window,
                        '삭제 완료',
                        f'프리셋 "{name}"이(가) 삭제되었습니다.'
                    )
                    return True
        except Exception as e:
            QMessageBox.warning(
                self.main_window,
                '오류',
                f'프리셋 삭제 중 오류가 발생했습니다: {str(e)}'
            )
        return False

    def load_preset(self, name):
        """저장된 프리셋 불러오기"""
        try:
            if name not in self.presets:
                QMessageBox.warning(
                    self.main_window,
                    '오류',
                    f'프리셋 "{name}"을(를) 찾을 수 없습니다.'
                )
                return False

            settings = self.presets[name]
            
            # 템플릿 설정 적용
            self.main_window.show_inner_box.setChecked(settings['template']['show_inner_box'])
            self.main_window.outer_box_color.setColor(settings['template']['outer_box_color'])
            self.main_window.inner_box_color.setColor(settings['template']['inner_box_color'])
            self.main_window.shadow_intensity.setValue(settings['template']['shadow_intensity'])

            # 프로필 설정 적용
            self.main_window.show_profile.setChecked(settings['profile']['show_profile'])
            self.main_window.show_profile_image.setChecked(settings['profile']['show_profile_image'])
            self.main_window.show_bot_name.setChecked(settings['profile']['show_bot_name'])
            self.main_window.show_tags.setChecked(settings['profile']['show_tags'])
            self.main_window.show_divider.setChecked(settings['profile']['show_divider'])
            self.main_window.frame_style.setCurrentText(settings['profile']['frame_style'])
            self.main_window.width_input.setValue(settings['profile']['width'])
            self.main_window.height_input.setValue(settings['profile']['height'])
            self.main_window.image_url.setText(settings['profile']['image_url'])
            self.main_window.profile_border_color.setColor(settings['profile']['profile_border_color'])

            # 봇 설정 적용
            self.main_window.bot_name.setText(settings['bot']['name'])
            self.main_window.bot_name_color.setColor(settings['bot']['name_color'])

            # 기존 태그 제거
            for i in reversed(range(self.main_window.tag_layout.count())):
                item = self.main_window.tag_layout.itemAt(i)
                if item:
                    if item.layout():
                        while item.layout().count():
                            widget = item.layout().takeAt(0).widget()
                            if widget:
                                widget.deleteLater()
                        self.main_window.tag_layout.removeItem(item)
                    elif item.widget():
                        item.widget().deleteLater()

            self.main_window.tag_boxes.clear()
            self.main_window.tag_colors.clear()

            # 새 태그 추가
            for tag in settings['tags']:
                self.main_window.add_new_tag()
                idx = len(self.main_window.tag_boxes) - 1
                self.main_window.tag_boxes[idx].setText(tag['text'])
                self.main_window.tag_colors[idx].setColor(tag['color'])

            # 구분선 설정 적용
            self.main_window.divider_style.setCurrentText(settings['divider']['style'])
            self.main_window.divider_thickness.setValue(settings['divider']['thickness'])
            self.main_window.divider_outer_color.setColor(settings['divider']['outer_color'])
            self.main_window.divider_inner_color.setColor(settings['divider']['inner_color'])
            self.main_window.divider_solid_color.setColor(settings['divider']['solid_color'])

            # 텍스트 설정 적용
            self.main_window.text_indent.setValue(settings['text']['indent'])
            self.main_window.dialog_color.setColor(settings['text']['dialog_color'])
            self.main_window.narration_color.setColor(settings['text']['narration_color'])
            self.main_window.dialog_bold.setChecked(settings['text']['dialog_bold'])
            self.main_window.remove_asterisk.setChecked(settings['text']['remove_asterisk'])
            self.main_window.convert_ellipsis.setChecked(settings['text']['convert_ellipsis'])

            # 기존 단어 변경 항목 제거
            for i in reversed(range(self.main_window.word_replace_layout.count())):
                widget = self.main_window.word_replace_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            # 새 단어 변경 항목 추가
            for word_replace in settings['word_replace']:
                entry = WordReplaceEntry(self.main_window.word_replace_container)
                entry.from_word.setText(word_replace['from'])
                entry.to_word.setText(word_replace['to'])
                self.main_window.word_replace_layout.addWidget(entry)

            # 설정 적용 후 UI 업데이트
            self.main_window.update_profile_element_states()
            self.main_window.update_preview()

            QMessageBox.information(
                self.main_window,
                '불러오기 완료',
                f'프리셋 "{name}"이(가) 성공적으로 적용되었습니다.'
            )
            return True

        except Exception as e:
            QMessageBox.warning(
                self.main_window,
                '오류',
                f'프리셋을 불러오는 중 오류가 발생했습니다: {str(e)}'
            )
            print(f"프리셋 불러오기 오류: {e}")
            return False


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))  # 이 부분이 변경됨
    return os.path.join(base_path, relative_path)

# 모던한 스타일 상수 정의
STYLES = {
    # 색상
    'primary': '#b0b2c6',
    'secondary': '#5856D6',
    'success': '#34C759',
    'background': '#FFFFFF',
    'surface': '#F2F2F7',
    'text': '#000000',
    'text_secondary': '#6C6C70',
    'border': '#C6C6C8',
    
    # 기본값
    'outer_box_color': '#ffffff',
    'inner_box_color': '#f8f9fa',
    'shadow_intensity': 8,
    'bot_name_color': '#4a4a4a',
    'tag_colors': ['#E3E3E8', '#E3E3E8', '#E3E3E8'],
    'divider_outer_color': '#b8bacf',
    'divider_inner_color': '#ffffff',
    'dialog_color': '#4a4a4a',
    'narration_color': '#4a4a4a',
    'profile_border_color': '#ffffff',
    'text_indent': 20,
    
    # 폰트
    'font_family': 'Segoe UI, Roboto, Arial, sans-serif',  # 수정된 폰트 패밀리
    'font_size_large': 16,
    'font_size_normal': 14,
    'font_size_small': 12,
    'font_weight_normal': 500,
    'font_weight_bold': 600,
    
    # 간격
    'spacing_large': 24,
    'spacing_normal': 16,
    'spacing_small': 8,
    
    # 둥근 모서리
    'radius_large': 16,
    'radius_normal': 8,
    'radius_small': 4,
}

TEMPLATE_PRESETS = {
    "커스텀": {
        "outer_box_color": "#ffffff",
        "inner_box_color": "#f8f9fa",
        "background_color": "#f8f9fa",  # 기존 inner_box_color와 동일
        "bot_name_color": "#4a4a4a",
        "tag_colors": ["#E3E3E8", "#E3E3E8", "#E3E3E8"],
        "divider_outer_color": "#b8bacf",
        "divider_inner_color": "#ffffff",
        "dialog_color": "#4a4a4a",
        "narration_color": "#4a4a4a",
        "profile_border_color": "#ffffff"
    },
    "모던 블루": {
        "outer_box_color": "#1a202c",
        "inner_box_color": "#2d3748",
        "background_color": "#2d3748",  # 기존 inner_box_color와 동일하게 유지
        "bot_name_color": "#90cdf4",
        "tag_colors": ["#2d3748", "#2d3748", "#2d3748"],
        "divider_outer_color": "#4a5568",
        "divider_inner_color": "#2d3748",
        "dialog_color": "#e2e8f0",
        "narration_color": "#cbd5e0",
        "profile_border_color": "#4a5568"
    },
    "다크 모드": {
        "outer_box_color": "#000000",
        "inner_box_color": "#0a0a0a",
        "background_color": "#0a0a0a",  # 기존 inner_box_color와 동일하게 유지
        "bot_name_color": "#ffffff",
        "tag_colors": [
            "#1a1a1a",
            "#262626",
            "#333333"
        ],
        "divider_outer_color": "#333333",
        "divider_inner_color": "#0a0a0a",
        "dialog_color": "#ffffff",
        "narration_color": "#e0e0e0",
        "profile_border_color": "#333333"
    },
    "로즈 골드": {
        "outer_box_color": "#ffffff",
        "inner_box_color": "#fff5f5",
        "background_color": "#fff1f1",  # 약간 더 진한 로즈 톤
        "bot_name_color": "#c53030",
        "tag_colors": ["#fed7d7", "#feb2b2", "#fc8181"],
        "divider_outer_color": "#fc8181",
        "divider_inner_color": "#ffffff",
        "dialog_color": "#2d3748",
        "narration_color": "#4a5568",
        "profile_border_color": "#feb2b2"
    },
    "민트 그린": {
        "outer_box_color": "#ffffff",
        "inner_box_color": "#f0fff4",
        "background_color": "#e7faea",  # 약간 더 진한 민트 톤
        "bot_name_color": "#2f855a",
        "tag_colors": ["#c6f6d5", "#9ae6b4", "#68d391"],
        "divider_outer_color": "#48bb78",
        "divider_inner_color": "#ffffff",
        "dialog_color": "#2d3748",
        "narration_color": "#4a5568",
        "profile_border_color": "#9ae6b4"   
    },
    "모던 퍼플": {
        "outer_box_color": "#ffffff",
        "inner_box_color": "#f8f5ff",
        "background_color": "#f5f0ff",
        "bot_name_color": "#6b46c1",
        "tag_colors": ["#e9d8fd", "#d6bcfa", "#b794f4"],
        "divider_outer_color": "#9f7aea",
        "divider_inner_color": "#ffffff",
        "dialog_color": "#4a5568",
        "narration_color": "#718096",
        "profile_border_color": "#9f7aea"
    }
}
# 기본 프로필 이미지 (placeholder)
DEFAULT_PROFILE_IMAGE = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH4wYJBhYRN2n7qQAAAB1pVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJTVBkLmUHAAAEiUlEQVR42u2dW2hcVRSGv3XOxEmTmTRp2kziJU0UqUVriy+CLxZfi1gUX3wTfPBJ8EkQwQteMFIfLFoQxQteMCJeULQoquKDgheCbdHWam0vMW3TJm0ymUzmnJk5e/kwt7SSOSdNOpN91v+0YQ577T3/f9bea6+99hgTExMTExMTExMTE5NbE2lNRapr+xUwD8gFEWB4dJQrAyfo6+1JXGsAD4vgSQgbj0EkLgcKqAocxeWkOJwgrr+1JR1CJovpKDxbgUfFY4vApgJJACIgHkioIghYgDCwLlCjsV4mE3YyELBDQRYEHVKOEhKQEYFMURaLsAhYPr5wYkBEGFOXIZcEtjE2DWgmWYagSEwGXWVxWvGKpcQR+qIW5wYsCm5K7DQXn4xSEu/Hw0J9LyeOg0e2RTgrmALZYEfIlDCHew6xvKjEpuXsKHiJcqNUqWAsEzFPt8QRxK+A/lCIU/lFtM8PsXdVmBdiZXyiNluIc6hrPxt6HYpkmGTa5CWbQ48cUBIFxMJjXuEALyaWcPp4DesWb2N/SnycGPPxqABfimIMSUBJpAYRDwXm5vXxQayaV2QZO4kTlJAvn7xgwqe3bkEAevKEJUWCiUQNIuCJ0lR3lb3HDpC32SZzk6QaE0EBRBhVDxEhLh4RD0Q9clQoFEhcwPd6BcwXGRIYU6VPhJj6FOARBo6ny9kYGuRo1zeMxEcoWxtlUEEFJKSAqjKkMKxCSISwQDEQUsETxRXBQ7BE8EQQVVxbKVCbEYHjwEsiZxAsgWVWnPq2GNUt7URo5GTNaZbVDnKnZdN0vJY3B7JZIw4t6pPGElx1cUUZE2FYlYgqloArQlCUAlXyVclWiKsyKoIliqseYVEUYVSVfhFCAlFVRgSiojjq4agQUyVPhDCAqBAVxRMlR4SQKq7CkAhRUVwRPIGwKo5ATABPsVWIq4cnQlCVuAoeEBTBUSWkEFElLEKBKDnq4QKOQESEYVXiqgQFwqpEFWSszTiqOCLY6hEX8LQ8hwc74OIcIVB9nJbmTr7rPMzg0EUcN0aWVo5n6AW27XB5YjfHA6V8r1kuEXFwhZAqriioKo4IUYGoCIUKeaqERMhWIU+VHFGGBIZViaq/fPl/OHIcXBRbBFshLkqOQESUiEJIBFuUQYVRVWz1CAmoCrZ6xFSxEQLqkSsQFigQxVXBFsUVGFPwRHBViSsEBBRBRQmJkqNg64R4iHi4ohQi2KLYAiEVXFVy1CMoSgQIihATxRXFq0mQHspmLmA8BRFQhJgqYVFsAVdASYiHCGFV8kSwx1NX4fV5ZrE9nMfF+BD5JQrFDsUWBEUIixBTxRbBBkSUMYGQKA5gixJXJSxQKEKY8fM4FWwEVyAmQlyEkCpxEYIK+QIB9chRGD/pE2KixFUJq2IrBEQJiRBRZUQgJEJQwRMQEYbVI6Yg6hFQwEU8EWyBoCqOQFggR5SQguv5OxGDIgQEHBWiAjGBoHrkC4RFGQMiAgHAdYW5IgSBEQHiEMWlQqBIICJCXAVHYNAVBgUyRYgJxBDiOHQrZIsy6qZRzxsmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJtPI3wlK8GXlSW/WAAAAAElFTkSuQmCC"

    

class ModernButton(QPushButton):
    """모던한 스타일의 버튼 컴포넌트"""
    def __init__(self, text, primary=False, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self.setup_style()
        
    def setup_style(self):
        style = f"""
            QPushButton {{
                background-color: {STYLES['primary'] if self.primary else STYLES['surface']};
                color: {'white' if self.primary else STYLES['text']};
                border: none;
                border-radius: {STYLES['radius_normal']}px;
                padding: 8px 16px;
                font-size: {STYLES['font_size_normal']}px;
                font-weight: {STYLES['font_weight_normal']};
            }}
            QPushButton:hover {{
                background-color: {'#9597a8' if self.primary else '#E5E5EA'};
            }}
            QPushButton:pressed {{
                background-color: {'#7a7c8a' if self.primary else '#D1D1D6'};
            }}
        """
        self.setStyleSheet(style)

class ModernColorButton(QPushButton):
    """색상 선택 버튼 컴포넌트"""
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.setFixedSize(32, 32)
        self.color = color
        self.setColor(color)
        # 새로 추가: 우클릭 메뉴 활성화
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def setColor(self, color):
        self.color = color
        style = f"""
            QPushButton {{
                background-color: {color};
                border: 2px solid {STYLES['border']};
                border-radius: {STYLES['radius_normal']}px;
            }}
            QPushButton:hover {{
                border: 2px solid {STYLES['primary']};
            }}
        """
        self.setStyleSheet(style)
        
    def get_color(self):
        return self.color

    # 새로 추가: 우클릭 메뉴 표시
    def show_context_menu(self, position):
        menu = QMenu(self)
        reset_action = menu.addAction("기본색으로 리셋")
        reset_action.triggered.connect(self.reset_color)
        menu.exec(self.mapToGlobal(position))

    # 새로 추가: 색상 리셋
    def reset_color(self):
        """색상을 기본값으로 리셋"""
        default_color = "#000000"  # 기본 검은색
        self.setColor(default_color)
        self.color = default_color

class ModernComboBox(QComboBox):
    """모던한 스타일의 콤보박스 컴포넌트"""
    def __init__(self, parent=None):
        super().__init__(parent)
        style = f"""
            QComboBox {{
                background-color: {STYLES['surface']};
                border: none;
                border-radius: {STYLES['radius_normal']}px;
                padding: 8px 12px;
                font-size: {STYLES['font_size_normal']}px;
                color: {STYLES['text']};
                min-width: 120px;
                font-weight: {STYLES['font_weight_normal']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {STYLES['surface']};
                border: 1px solid {STYLES['border']};
                border-radius: {STYLES['radius_normal']}px;
                selection-background-color: {STYLES['primary']};
                selection-color: white;
                color: {STYLES['text']};
            }}
            QComboBox::item:selected {{
                background-color: {STYLES['primary']};
                color: white;
            }}
            QComboBox::item:hover {{
                background-color: {STYLES['border']};
            }}
        """
        self.setStyleSheet(style)
        
    def wheelEvent(self, event):
        """마우스 휠 이벤트 무시"""
        event.ignore()

class ModernCheckBox(QCheckBox):
    """모던한 스타일의 체크박스 컴포넌트"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        style = f"""
            QCheckBox {{
                font-size: {STYLES['font_size_normal']}px;
                color: {STYLES['text']};
                font-weight: {STYLES['font_weight_normal']};
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid {STYLES['border']};
            }}
            QCheckBox::indicator:unchecked {{
                background-color: rgba(0, 0, 0, 0.5);  /* 검은색 50% 투명도 */
            }}
            QCheckBox::indicator:checked {{
                background-color: #32D74B;  /* 연한 초록색 */
                border-color: #32D74B;
            }}
        """
        self.setStyleSheet(style)

class SettingsGroup(QWidget):
    """설정 그룹 컨테이너 컴포넌트"""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, STYLES['spacing_large'])
        
        # 헤더
        header = QLabel(title)
        header.setFont(QFont(STYLES['font_family'], STYLES['font_size_large'], STYLES['font_weight_bold']))
        layout.addWidget(header)
        
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {STYLES['border']};")
        layout.addWidget(line)
        
        # 콘텐츠 컨테이너
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, STYLES['spacing_small'], 0, 0)
        self.content_layout.setSpacing(STYLES['spacing_small'])
        layout.addWidget(self.content)
        
    def addWidget(self, widget):
        self.content_layout.addWidget(widget)
        
    def addLayout(self, layout):
        self.content_layout.addLayout(layout)

class ModernSpinBox(QSpinBox):
    """모던한 스타일의 스핀박스 컴포넌트"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QSpinBox {{
                background-color: {STYLES['surface']};
                border: none;
                border-radius: {STYLES['radius_normal']}px;
                padding: 8px 12px;
                font-size: {STYLES['font_size_normal']}px;
                color: {STYLES['text']};
                font-weight: {STYLES['font_weight_normal']};
                min-width: 40px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                border: none;
                width: 20px;
            }}
        """)
        
    def wheelEvent(self, event):
        """마우스 휠 이벤트 무시"""
        event.ignore()

class WordReplaceEntry(QWidget):
    """단어 변경을 위한 입력 컴포넌트"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 변환할 단어 입력
        self.from_word = QLineEdit()
        self.from_word.setPlaceholderText("변환할 단어")
        layout.addWidget(self.from_word)
        
        # 화살표 라벨
        arrow_label = QLabel("→")
        layout.addWidget(arrow_label)
        
        # 변환될 단어 입력
        self.to_word = QLineEdit()
        self.to_word.setPlaceholderText("변환될 단어")
        layout.addWidget(self.to_word)
        
        # 삭제 버튼
        delete_btn = ModernButton("삭제")
        delete_btn.setFixedWidth(60)
        delete_btn.clicked.connect(self.remove_self)
        layout.addWidget(delete_btn)

    def remove_self(self):
        """안전하게 자신을 제거"""
        self.setParent(None)  # 부모로부터 분리
        self.deleteLater()    # 나중에 삭제되도록 예약

class ImageUrlEntry(QWidget):
    """이미지 URL 입력을 위한 컴포넌트"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 이미지 태그 입력
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("이미지 태그 (예: Orca_surprised)")
        layout.addWidget(self.tag_input)
        
        # 화살표 라벨
        arrow_label = QLabel("→")
        layout.addWidget(arrow_label)
        
        # URL 입력
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("이미지 URL")
        layout.addWidget(self.url_input)
        
        # 삭제 버튼
        delete_btn = ModernButton("삭제")
        delete_btn.setFixedWidth(60)
        delete_btn.clicked.connect(self.remove_self)
        layout.addWidget(delete_btn)

    def remove_self(self):
        """안전하게 자신을 제거"""
        self.setParent(None)
        self.deleteLater()

    def to_dict(self):
        """현재 매핑 정보를 딕셔너리로 반환"""
        return {
            'tag': self.tag_input.text().strip(),
            'url': self.url_input.text().strip()
        }

    def from_dict(self, data):
        """딕셔너리에서 매핑 정보 로드"""
        self.tag_input.setText(data.get('tag', ''))
        self.url_input.setText(data.get('url', ''))

class TagEntry(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 태그 텍스트 입력
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("태그 입력")
        layout.addWidget(self.tag_input)
        
        # 색상 설정 컨테이너
        color_container = QHBoxLayout()
        
        # 배경색/테두리색 레이블
        self.color_label = QLabel("배경색")
        color_container.addWidget(self.color_label)
        
        # 색상 선택 버튼
        self.color_btn = ModernColorButton("#E3E3E8")
        self.color_btn.clicked.connect(self.choose_color)
        color_container.addWidget(self.color_btn)
        
        # 투명 배경 토글
        self.transparent_bg = ModernCheckBox("투명 배경")
        self.transparent_bg.stateChanged.connect(self.update_color_label)
        color_container.addWidget(self.transparent_bg)
        
        layout.addLayout(color_container)
        
        # 삭제 버튼
        delete_btn = ModernButton("삭제")
        delete_btn.setFixedWidth(60)
        delete_btn.clicked.connect(self.remove_self)
        layout.addWidget(delete_btn)

    def update_color_label(self):
        """투명 배경 설정에 따라 레이블 텍스트 변경"""
        self.color_label.setText("테두리색" if self.transparent_bg.isChecked() else "배경색")

    def is_transparent(self):
        """투명 배경 사용 여부 반환"""
        return self.transparent_bg.isChecked()
    def choose_color(self, target):
        """색상 선택 다이얼로그"""
        color = QColorDialog.getColor()
        if color.isValid():
            if target == "outer_box":
                self.outer_box_color.setColor(color.name())
            elif target == "inner_box":
                self.inner_box_color.setColor(color.name())
            elif target == "profile_border":
                self.profile_border_color.setColor(color.name())
            elif target == "bot_name":
                self.bot_name_color.setColor(color.name())
            elif target == "dialog":
                self.dialog_color.setColor(color.name())
            elif target == "narration":
                self.narration_color.setColor(color.name())
            elif target == "divider_outer":
                self.divider_outer_color.setColor(color.name())
            elif target == "divider_inner":
                self.divider_inner_color.setColor(color.name())
            elif target == "divider_solid":
                self.divider_solid_color.setColor(color.name())
    
    def remove_self(self):
        """안전하게 자신을 제거"""
        self.setParent(None)
        self.deleteLater()

    def get_tag_text(self):
        """태그 텍스트 반환"""
        return self.tag_input.text()

    def get_tag_color(self):
        """태그 색상 반환"""
        return self.color_btn.get_color()

class ModernLogGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.preview_timer = None
        self.card_handler = CharacterCardHandler()
        self.asset_name_img_tag_map = {}
        self.image_cache = ImageCache()
        self.mapping_manager = MappingManager(self)  # 이 줄을 추가합니다

        # 아이콘 설정에 resource_path 사용
        icon_path = resource_path('log_icon.ico')
        self.setWindowIcon(QIcon(icon_path))
        
        # 다크모드 변경 감지
        self.color_scheme_handler = QApplication.instance().styleHints()
        self.color_scheme_handler.colorSchemeChanged.connect(self.update_color_scheme)
        
        # 프리셋 매니저 초기화
        self.preset_manager = PresetManager(self)
        
        self.init_ui()
        self.init_profile_image_handlers()

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("LogGenerator Pro")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        self.setup_styles()

        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(STYLES['spacing_large'], STYLES['spacing_large'], 
                                    STYLES['spacing_large'], STYLES['spacing_large'])
        main_layout.setSpacing(STYLES['spacing_normal'])
        
        # === Splitter 추가 ===
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(12)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background: transparent;
                margin: 0 5px;
            }
            QSplitter::handle:horizontal {
                image: url(none);
                width: 12px;
                background-color: transparent;
                border-left: 2px solid #cccccc;
                margin: 0 5px;
            }
            QSplitter::handle:horizontal:hover {
                border-left: 4px solid #999999;
                margin: 0 4px;
            }
            QSplitter::handle:horizontal:pressed {
                border-left: 4px solid #666666;
                margin: 0 4px;
            }
        """)
        
        # === 왼쪽 패널 (설정) ===
        left_panel = self.create_settings_panel()
        left_panel.setMinimumWidth(0)      # 완전히 접을 수 있도록
        left_panel.setMaximumWidth(800)    # 최대 너비 여유있게 증가
        
        # === 오른쪽 패널 (입출력) ===
        right_panel = self.create_io_panel()
        right_panel.setMinimumWidth(0)     # 완전히 접을 수 있도록
        # 최대 너비 제한 제거 - 전체화면에서도 자유롭게 조절 가능
        
        # 패널들을 splitter에 추가
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # splitter 크기 비율 설정 - 더 유연하게 조절
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        # 초기 크기를 화면 크기에 비례하여 설정
        total_width = self.width()
        splitter.setSizes([total_width // 3, (total_width * 2) // 3])
        
        # splitter를 메인 레이아웃에 추가
        main_layout.addWidget(splitter)

    def setup_styles(self):
        """전역 스타일 설정"""
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {STYLES['background']};
                font-weight: {STYLES['font_weight_normal']};
            }}
            QLabel {{
                font-size: {STYLES['font_size_normal']}px;
                color: {STYLES['text']};
                font-weight: {STYLES['font_weight_normal']};
            }}
            QLineEdit {{
                background-color: {STYLES['surface']};
                border: none;
                border-radius: {STYLES['radius_normal']}px;
                padding: 8px 12px;
                font-size: {STYLES['font_size_normal']}px;
                color: {STYLES['text']};
                font-weight: {STYLES['font_weight_normal']};
            }}
            QTextEdit {{
                background-color: {STYLES['surface']};
                border: none;
                border-radius: {STYLES['radius_normal']}px;
                padding: 12px;
                font-size: {STYLES['font_size_normal']}px;
                color: {STYLES['text']};
                font-weight: {STYLES['font_weight_normal']};
            }}
            
            /* 수직 스크롤바 스타일 */
            QScrollBar:vertical {{
                border: none;
                background-color: {STYLES['background']};
                width: 10px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: #A0A0A0;
                min-height: 30px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #808080;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: none;
            }}
            
            /* 수평 스크롤바 스타일 */
            QScrollBar:horizontal {{
                border: none;
                background-color: {STYLES['background']};
                height: 10px;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background-color: #A0A0A0;
                min-width: 30px;
                border-radius: 5px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: #808080;
            }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """)

    def update_color_scheme(self):
        """다크모드 전환 처리"""
        is_dark = self.color_scheme_handler.colorScheme() == Qt.ColorScheme.Dark
        
        new_styles = {
            'background': '#1C1C1E' if is_dark else '#FFFFFF',
            'surface': '#2C2C2E' if is_dark else '#F2F2F7',
            'text': '#FFFFFF' if is_dark else '#000000',
            'text_secondary': '#98989D' if is_dark else '#6C6C70',
            'border': '#3A3A3C' if is_dark else '#C6C6C8',
        }
        
        STYLES.update(new_styles)
        self.setup_styles()

    def get_scrollbar_style(self):
        """스크롤바 스타일 반환"""
        return f"""
            QScrollArea {{
                background-color: {STYLES['background']};
                border: none;
            }}
            QScrollBar:vertical {{
                border: none;
                background-color: {STYLES['background']};
                width: 10px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: #A0A0A0;
                min-height: 30px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #808080;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QScrollBar:horizontal {{
                border: none;
                background-color: {STYLES['background']};
                height: 10px;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background-color: #A0A0A0;
                min-width: 30px;
                border-radius: 5px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: #808080;
            }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """
    def create_settings_panel(self):
        """설정 패널 생성"""
        class MinSizeWidget(QWidget):
            def minimumSizeHint(self):
                return QSize(0, 0)
        
        panel = MinSizeWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(self.get_scrollbar_style())
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(STYLES['spacing_large'])
        
        # 각 설정 그룹 생성
        template_group = self.create_template_settings()
        profile_group = self.create_profile_settings()
        bot_group = self.create_bot_settings()
        tag_group = self.create_tag_settings()
        divider_group = self.create_divider_settings()
        text_group = self.create_text_settings()
        word_replace_group = self.create_word_replace_settings()
        asset_group = self.create_asset_settings()
        
        # 설정 그룹들을 스크롤 레이아웃에 추가
        scroll_layout.addWidget(template_group)
        scroll_layout.addWidget(profile_group)
        scroll_layout.addWidget(bot_group)
        scroll_layout.addWidget(tag_group)
        scroll_layout.addWidget(divider_group)
        scroll_layout.addWidget(text_group)
        scroll_layout.addWidget(word_replace_group)
        scroll_layout.addWidget(asset_group)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return panel

    def create_template_settings(self):
        """템플릿 설정 그룹 생성"""
        group = SettingsGroup("템플릿 설정")
        
        # 프리셋 관리 버튼 추가
        preset_btn = self.create_preset_button()
        group.addWidget(preset_btn)

        # 템플릿 선택 콤보박스 추가
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("템플릿"))
        self.template_combo = ModernComboBox()
        self.template_combo.addItems(TEMPLATE_PRESETS.keys())
        self.template_combo.currentTextChanged.connect(self.apply_template)
        template_layout.addWidget(self.template_combo)
        group.addLayout(template_layout)

        # 외부 박스 표시 여부
        inner_box_layout = QHBoxLayout()
        self.show_inner_box = ModernCheckBox("외부 박스 표시")
        self.show_inner_box.setChecked(False)
        inner_box_layout.addWidget(self.show_inner_box)
        group.addLayout(inner_box_layout)

        # 박스 색상
        box_colors = QWidget()
        box_layout = QVBoxLayout(box_colors)
        box_layout.setSpacing(STYLES['spacing_normal'])

        # 외부 박스 색상
        outer_box = QHBoxLayout()
        outer_box.addWidget(QLabel("외부 박스 색상"))
        self.outer_box_color = ModernColorButton(STYLES['outer_box_color'])
        self.outer_box_color.clicked.connect(lambda: self.choose_color("outer_box"))
        outer_box.addWidget(self.outer_box_color)
        box_layout.addLayout(outer_box)

        # 내부 박스 색상
        inner_box = QHBoxLayout()
        inner_box.addWidget(QLabel("내부 박스 색상"))
        self.inner_box_color = ModernColorButton(STYLES['inner_box_color'])
        self.inner_box_color.clicked.connect(lambda: self.choose_color("inner_box"))
        inner_box.addWidget(self.inner_box_color)
        box_layout.addLayout(inner_box)

        group.addWidget(box_colors)

        # 그림자 설정 (UI는 숨기되 기능은 유지)
        shadow_widget = QWidget()
        shadow_layout = QHBoxLayout(shadow_widget)
        shadow_layout.addWidget(QLabel("그림자 강도"))
        self.shadow_intensity = ModernSpinBox()
        self.shadow_intensity.setRange(0, 40)
        self.shadow_intensity.setValue(STYLES['shadow_intensity'])
        shadow_layout.addWidget(self.shadow_intensity)
        shadow_widget.hide()  # 위젯을 숨김
        group.addWidget(shadow_widget)

        return group

    def update_box_settings(self, show_outer_box):
        """박스 설정 UI 업데이트"""
        self.outer_box_container.setVisible(show_outer_box)
        self.inner_box_container.setVisible(show_outer_box)
        self.single_box_container.setVisible(not show_outer_box)
        
        # 외부 박스가 비활성화될 때 단일 박스 색상을 내부 박스 색상으로 설정
        if not show_outer_box:
            self.single_box_color.setColor(self.inner_box_color.get_color())


    def apply_template(self):
        """선택된 템플릿 적용"""
        template_name = self.template_combo.currentText()
        template = TEMPLATE_PRESETS[template_name]

        # 각 색상 설정 적용
        self.outer_box_color.setColor(template["outer_box_color"])
        self.inner_box_color.setColor(template["inner_box_color"])
        self.bot_name_color.setColor(template["bot_name_color"])
        self.profile_border_color.setColor(template["profile_border_color"])
        self.dialog_color.setColor(template["dialog_color"])
        self.narration_color.setColor(template["narration_color"])
        self.divider_outer_color.setColor(template["divider_outer_color"])
        self.divider_inner_color.setColor(template["divider_inner_color"])

        # 태그 색상 설정 - 안전하게 처리
        for i, color_btn in enumerate(self.tag_colors):
            if i < len(template["tag_colors"]):  # 템플릿의 색상 개수만큼만 적용
                color_btn.setColor(template["tag_colors"][i])
            else:
                # 템플릿의 색상이 부족한 경우 마지막 색상 사용
                color_btn.setColor(template["tag_colors"][-1])

    def create_profile_settings(self):
        """프로필 설정 그룹 생성"""
        group = SettingsGroup("프로필 설정")

        # 프로필 요소별 표시 설정
        profile_elements_layout = QVBoxLayout()
        
        # 전체 프로필 표시 설정
        show_profile_layout = QHBoxLayout()
        self.show_profile = ModernCheckBox("프로필 표시")
        self.show_profile.setChecked(True)
        self.show_profile.stateChanged.connect(self.update_profile_element_states)
        show_profile_layout.addWidget(self.show_profile)
        profile_elements_layout.addLayout(show_profile_layout)
        
        # 개별 요소 표시 설정
        elements_container = QWidget()
        elements_layout = QVBoxLayout(elements_container)
        elements_layout.setContentsMargins(20, 0, 0, 0)  # 왼쪽 들여쓰기
        
        # 프로필 이미지 표시 설정
        show_image_layout = QHBoxLayout()
        self.show_profile_image = ModernCheckBox("프로필 이미지 표시")
        self.show_profile_image.setChecked(True)
        show_image_layout.addWidget(self.show_profile_image)
        elements_layout.addLayout(show_image_layout)
        
        # 봇 이름 표시 설정
        show_name_layout = QHBoxLayout()
        self.show_bot_name = ModernCheckBox("봇 이름 표시")
        self.show_bot_name.setChecked(True)
        show_name_layout.addWidget(self.show_bot_name)
        elements_layout.addLayout(show_name_layout)
        
        # 태그 표시 설정
        show_tags_layout = QHBoxLayout()
        self.show_tags = ModernCheckBox("태그 표시")
        self.show_tags.setChecked(True)
        show_tags_layout.addWidget(self.show_tags)
        elements_layout.addLayout(show_tags_layout)
        
        # 구분선 표시 설정
        show_divider_layout = QHBoxLayout()
        self.show_divider = ModernCheckBox("구분선 표시")
        self.show_divider.setChecked(True)
        show_divider_layout.addWidget(self.show_divider)
        elements_layout.addLayout(show_divider_layout)
        
        profile_elements_layout.addWidget(elements_container)
        group.addLayout(profile_elements_layout)

        # 프레임 스타일 선택 부분 수정
        frame_style_layout = QHBoxLayout()
        frame_style_layout.addWidget(QLabel("프레임 스타일"))
        # 프레임 스타일 선택
        self.frame_style = ModernComboBox()
        self.frame_style.addItems(["배너", "동그라미", "직사각형"])
        self.frame_style.currentTextChanged.connect(self.update_size_inputs)
        frame_style_layout.addWidget(self.frame_style)
        group.addLayout(frame_style_layout)
        
        # 크기 제한 안내 라벨
        self.size_info_label = QLabel()
        self.size_info_label.setStyleSheet(f"color: {STYLES['text_secondary']};")
        group.addWidget(self.size_info_label)

        # 크기 설정 컨테이너
        size_group = QWidget()
        self.size_layout = QGridLayout(size_group)
        
        # 크기/너비 설정
        self.size_label = QLabel("크기")
        self.size_layout.addWidget(self.size_label, 0, 0)
        self.width_input = ModernSpinBox()
        self.width_input.setRange(20, 300)
        self.width_input.setValue(80)
        self.width_input.setSuffix("px")
        self.size_layout.addWidget(self.width_input, 0, 1)
        
        # 높이 설정
        self.height_label = QLabel("높이")
        self.size_layout.addWidget(self.height_label, 1, 0)
        self.height_input = ModernSpinBox()
        self.height_input.setRange(20, 300)
        self.height_input.setValue(80)
        self.height_input.setSuffix("px")
        self.size_layout.addWidget(self.height_input, 1, 1)
        
        group.addWidget(size_group)

        # URL 입력
        url_layout = QVBoxLayout()
        url_layout.addWidget(QLabel("이미지 URL"))
        self.image_url = QLineEdit()
        self.image_url.setPlaceholderText("https://example.com/image.jpg")
        url_layout.addWidget(self.image_url)
        group.addLayout(url_layout)

        # 이미지 스타일 설정 (URL 입력칸 바로 아래)
        style_layout = QVBoxLayout()
        style_layout.setContentsMargins(0, STYLES['spacing_small'], 0, 0)
        
        # 테두리 설정
        border_layout = QHBoxLayout()
        self.show_profile_border = ModernCheckBox("테두리 표시")
        self.show_profile_border.setChecked(True)
        border_layout.addWidget(self.show_profile_border)
        
        border_layout.addWidget(QLabel("색상"))
        self.profile_border_color = ModernColorButton(STYLES['profile_border_color'])
        self.profile_border_color.clicked.connect(lambda: self.choose_color("profile_border"))
        border_layout.addWidget(self.profile_border_color)
        border_layout.addStretch()
        style_layout.addLayout(border_layout)
        
        # 그림자 설정 - 단순히 ON/OFF만 가능하도록 수정
        shadow_layout = QHBoxLayout()
        self.show_profile_shadow = ModernCheckBox("그림자 효과")
        self.show_profile_shadow.setChecked(True)
        shadow_layout.addWidget(self.show_profile_shadow)
        shadow_layout.addStretch()
        style_layout.addLayout(shadow_layout)
        
        group.addLayout(style_layout)

        # 상태 업데이트 연결
        self.show_profile_border.stateChanged.connect(self.update_profile_style_states)
        self.show_profile_shadow.stateChanged.connect(self.update_profile_style_states)

        # 초기 상태 설정
        self.update_size_inputs(self.frame_style.currentText())
        self.update_profile_element_states()
        self.update_profile_style_states()

        return group

    def update_profile_element_states(self):
        """프로필 요소들의 활성화 상태 업데이트"""
        is_profile_enabled = self.show_profile.isChecked()
        
        # 하위 요소들의 체크박스 활성화/비활성화
        self.show_profile_image.setEnabled(is_profile_enabled)
        self.show_bot_name.setEnabled(is_profile_enabled)
        self.show_tags.setEnabled(is_profile_enabled)
        self.show_divider.setEnabled(is_profile_enabled)
        
        # 프로필 이미지 관련 UI 요소들
        self.frame_style.setEnabled(is_profile_enabled and self.show_profile_image.isChecked())
        self.width_input.setEnabled(is_profile_enabled and self.show_profile_image.isChecked())
        self.height_input.setEnabled(is_profile_enabled and self.show_profile_image.isChecked())
        self.image_url.setEnabled(is_profile_enabled and self.show_profile_image.isChecked())
        self.profile_border_color.setEnabled(is_profile_enabled and self.show_profile_image.isChecked())

    def update_size_inputs(self, style):
        """프레임 스타일에 따라 기본 크기값과 권장 사이즈 정보 업데이트"""
        if style == "동그라미":
            # 동그라미는 크기 입력만 표시
            self.size_label.setText("크기")
            self.size_label.show()
            self.width_input.show()
            self.width_input.setValue(80)
            self.width_input.setEnabled(True)
            self.height_label.hide()
            self.height_input.hide()
            size_info = "※ 크기 20~300px\n권장 이미지: 200x200px 정사각형"
            
        elif style == "배너":
            # 배너는 모든 크기 조절 UI 숨김
            self.size_label.hide()
            self.width_input.hide()
            self.height_label.hide()
            self.height_input.hide()
            size_info = "※ 권장 이미지: 1200x400px (3:1 비율)"
            
        else:  # 직사각형
            self.size_label.setText("크기")
            self.size_label.show()
            self.width_input.show()
            self.width_input.setValue(120)
            self.width_input.setEnabled(True)
            self.height_label.show()
            self.height_input.show()
            self.height_input.setValue(80)
            size_info = "※ 크기 제한: 20~300px\n권장 이미지: 300x200px (3:2 비율)"
        
        # 권장 사이즈 정보를 보여주는 레이블 스타일 설정
        self.size_info_label.setText(size_info)
        self.size_info_label.setStyleSheet(f"""
            color: {STYLES['text_secondary']};
            font-size: 12px;
            padding: 8px;
            background-color: {STYLES['surface']};
            border-radius: 4px;
            margin-top: 4px;
        """)

    def create_bot_settings(self):
        """봇 설정 그룹 생성"""
        group = SettingsGroup("봇 설정")
        
        # 봇 이름
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("봇 이름"))
        self.bot_name = QLineEdit()
        self.bot_name.setPlaceholderText("봇 이름을 입력하세요")
        name_layout.addWidget(self.bot_name)
        
        # 봇 이름 색상
        self.bot_name_color = ModernColorButton(STYLES['bot_name_color'])
        self.bot_name_color.clicked.connect(lambda: self.choose_color("bot_name"))
        name_layout.addWidget(QLabel("색상"))
        name_layout.addWidget(self.bot_name_color)
        
        group.addLayout(name_layout)
        return group

    def create_tag_settings(self):
            """태그 설정 그룹 생성"""
            group = SettingsGroup("태그 설정")
        
            # 기존 리스트 유지 (다른 메서드들과의 호환성을 위해)
            self.tag_boxes = []
            self.tag_colors = []
            self.tag_transparent = []  # 투명 배경 설정 저장용 리스트 추가
        
            # 태그 입력 컨테이너
            self.tag_container = QWidget()
            self.tag_layout = QVBoxLayout(self.tag_container)
            self.tag_layout.setSpacing(STYLES['spacing_small'])
        
            # 기본 태그 3개 추가
            default_tags = ["모델", "프롬프트", "번역"]
            for i, default_tag in enumerate(default_tags):
                tag_layout = QHBoxLayout()
            
                # 태그 텍스트
                tag_input = QLineEdit()
                tag_input.setPlaceholderText(f"태그 {i+1}")
                tag_input.setText(default_tag)
                tag_layout.addWidget(tag_input)
            
                # 색상 설정 컨테이너
                color_container = QHBoxLayout()
                
                # 배경색/테두리색 레이블
                color_label = QLabel("배경색")
                color_container.addWidget(color_label)
                
                # 태그 색상
                color_btn = ModernColorButton(STYLES['tag_colors'][i])
                color_btn.clicked.connect(lambda checked, idx=i: self.choose_tag_color(idx))
                color_container.addWidget(color_btn)
                
                # 투명 배경 토글 추가
                transparent_check = ModernCheckBox("투명 배경")
                transparent_check.stateChanged.connect(lambda state, label=color_label: 
                                                    label.setText("테두리색" if state else "배경색"))
                color_container.addWidget(transparent_check)
                
                tag_layout.addLayout(color_container)
            
                # 삭제 버튼 추가
                delete_btn = ModernButton("삭제")
                delete_btn.setFixedWidth(60)
                delete_btn.clicked.connect(lambda checked, layout=tag_layout: self.remove_tag(layout))
                tag_layout.addWidget(delete_btn)
            
                # 리스트에 추가
                self.tag_boxes.append(tag_input)
                self.tag_colors.append(color_btn)
                self.tag_transparent.append(transparent_check)
                self.tag_layout.addLayout(tag_layout)
        
            group.addWidget(self.tag_container)
        
            # 태그 추가 버튼
            add_btn = ModernButton("+ 태그 추가")
            add_btn.clicked.connect(self.add_new_tag)
            group.addWidget(add_btn)
        
            return group

    def add_new_tag(self):
        """새 태그 추가"""
        tag_layout = QHBoxLayout()
        
        # 태그 텍스트
        tag_input = QLineEdit()
        tag_input.setPlaceholderText(f"태그 {len(self.tag_boxes) + 1}")
        tag_layout.addWidget(tag_input)
        
        # 색상 설정 컨테이너
        color_container = QHBoxLayout()
        
        # 배경색/테두리색 레이블
        color_label = QLabel("배경색")
        color_container.addWidget(color_label)
        
        # 태그 색상
        color_btn = ModernColorButton(STYLES['tag_colors'][0])
        tag_idx = len(self.tag_colors)
        color_btn.clicked.connect(lambda checked, idx=tag_idx: self.choose_tag_color(idx))
        color_container.addWidget(color_btn)
        
        # 투명 배경 토글
        transparent_check = ModernCheckBox("투명 배경")
        transparent_check.stateChanged.connect(lambda state, label=color_label: 
                                            label.setText("테두리색" if state else "배경색"))
        color_container.addWidget(transparent_check)
        
        tag_layout.addLayout(color_container)
        
        # 태그 레이아웃을 담을 컨테이너 위젯
        container = QWidget()
        container.setLayout(tag_layout)
        
        # 삭제 버튼
        delete_btn = ModernButton("삭제")
        delete_btn.setFixedWidth(60)
        delete_btn.clicked.connect(lambda: self.remove_tag(container))
        tag_layout.addWidget(delete_btn)
        
        # 리스트에 추가
        self.tag_boxes.append(tag_input)
        self.tag_colors.append(color_btn)
        self.tag_transparent.append(transparent_check)
        
        # 레이아웃에 추가
        self.tag_layout.addWidget(container)

    def remove_tag(self, container):
        """태그 삭제"""
        # 최소 1개의 태그는 유지
        if len(self.tag_boxes) <= 1:
            return
        
        try:
            # 컨테이너의 인덱스 찾기
            idx = -1
            for i in range(self.tag_layout.count()):
                if self.tag_layout.itemAt(i).widget() == container:
                    idx = i
                    break
            
            if idx >= 0:
                # 리스트에서 제거
                if idx < len(self.tag_boxes):
                    self.tag_boxes.pop(idx)
                    self.tag_colors.pop(idx)
                    self.tag_transparent.pop(idx)
                
                # 위젯 제거
                container.deleteLater()
                self.tag_layout.removeWidget(container)
        except Exception as e:
            print(f"태그 삭제 중 오류 발생: {str(e)}")   
        

    def create_divider_settings(self):
        """구분선 설정 그룹 생성"""
        group = SettingsGroup("구분선 설정")
        
        # 스타일 선택
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("스타일"))
        self.divider_style = ModernComboBox()
        self.divider_style.addItems(["그라데이션", "단색"])
        self.divider_style.currentTextChanged.connect(self.toggle_divider_color_settings)
        style_layout.addWidget(self.divider_style)
        group.addLayout(style_layout)

        # 굵기 설정
        thickness_layout = QHBoxLayout()
        thickness_layout.addWidget(QLabel("굵기"))
        self.divider_thickness = ModernSpinBox()
        self.divider_thickness.setRange(1, 4)
        self.divider_thickness.setValue(1)
        self.divider_thickness.setSuffix("px")
        self.divider_thickness.setFixedWidth(70)
        thickness_layout.addWidget(self.divider_thickness)
        
        # 설명 레이블 추가
        info_label = QLabel("(1~4px)")
        info_label.setStyleSheet(f"color: {STYLES['text_secondary']};")
        thickness_layout.addWidget(info_label)
        
        # 나머지 공간을 채우기 위한 스트레치 추가
        thickness_layout.addStretch()
        
        group.addLayout(thickness_layout)  # 여기서 한 번만 추가!
        
        # 그라데이션 설정
        # ... (나머지 코드는 그대로 유지)
        
        # 그라데이션 설정
        self.gradient_settings = QWidget()
        gradient_layout = QVBoxLayout(self.gradient_settings)
        gradient_layout.setSpacing(STYLES['spacing_normal'])
        
        # 외부 색상
        outer_color_layout = QHBoxLayout()
        outer_color_layout.addWidget(QLabel("외부 색상"))
        self.divider_outer_color = ModernColorButton(STYLES['divider_outer_color'])
        self.divider_outer_color.clicked.connect(lambda: self.choose_color("divider_outer"))
        outer_color_layout.addWidget(self.divider_outer_color)
        gradient_layout.addLayout(outer_color_layout)
        
        # 내부 색상
        inner_color_layout = QHBoxLayout()
        inner_color_layout.addWidget(QLabel("내부 색상"))
        self.divider_inner_color = ModernColorButton(STYLES['divider_inner_color'])
        self.divider_inner_color.clicked.connect(lambda: self.choose_color("divider_inner"))
        inner_color_layout.addWidget(self.divider_inner_color)
        gradient_layout.addLayout(inner_color_layout)
        
        group.addWidget(self.gradient_settings)
        
        # 단색 설정
        self.solid_settings = QWidget()
        solid_layout = QHBoxLayout(self.solid_settings)
        solid_layout.addWidget(QLabel("선 색상"))
        self.divider_solid_color = ModernColorButton(STYLES['divider_outer_color'])
        self.divider_solid_color.clicked.connect(lambda: self.choose_color("divider_solid"))
        solid_layout.addWidget(self.divider_solid_color)
        
        group.addWidget(self.solid_settings)
        self.toggle_divider_color_settings(self.divider_style.currentText())
        
        return group

    def create_text_settings(self):
        """텍스트 설정 그룹 생성"""
        group = SettingsGroup("텍스트 설정")
        
        # 들여쓰기 컨테이너
        indent_container = QWidget()
        indent_layout = QVBoxLayout(indent_container)
        indent_layout.setSpacing(STYLES['spacing_small'])
        
        # 들여쓰기 활성화 체크박스
        self.use_text_indent = ModernCheckBox("문단 들여쓰기 사용")
        self.use_text_indent.setChecked(True)  # 기본값은 활성화
        self.use_text_indent.stateChanged.connect(self.update_indent_state)
        indent_layout.addWidget(self.use_text_indent)
        
        # 들여쓰기 크기 설정
        indent_size_layout = QHBoxLayout()
        indent_size_layout.setContentsMargins(20, 0, 0, 0)  # 왼쪽 여백으로 하위 설정임을 표시
        
        indent_size_layout.addWidget(QLabel("들여쓰기 크기"))
        self.text_indent = ModernSpinBox()
        self.text_indent.setRange(0, 100)  # 범위 설정
        self.text_indent.setValue(STYLES['text_indent'])
        self.text_indent.setSuffix("px")
        indent_size_layout.addWidget(self.text_indent)
        indent_layout.addLayout(indent_size_layout)
        
        # 들여쓰기 크기 제한 안내
        indent_info = QLabel("※ 들여쓰기 0~100px")
        indent_info.setStyleSheet(f"color: {STYLES['text_secondary']};")
        indent_info.setContentsMargins(20, 0, 0, 0)  # 왼쪽 여백 추가
        indent_layout.addWidget(indent_info)
        
        group.addWidget(indent_container)
        
        # 텍스트 크기 설정
        text_size_container = QWidget()
        text_size_layout = QVBoxLayout(text_size_container)
        text_size_layout.setSpacing(STYLES['spacing_small'])
        
        # 텍스트 크기 활성화 체크박스
        self.use_text_size = ModernCheckBox("텍스트 크기 조절 사용")
        self.use_text_size.setChecked(False)  # 기본값은 비활성화
        self.use_text_size.stateChanged.connect(self.update_text_size_state)
        text_size_layout.addWidget(self.use_text_size)
        
        # 텍스트 크기 설정
        text_size_control_layout = QHBoxLayout()
        text_size_control_layout.setContentsMargins(20, 0, 0, 0)  # 왼쪽 여백으로 하위 설정임을 표시
        
        text_size_control_layout.addWidget(QLabel("텍스트 크기"))
        self.text_size = ModernSpinBox()
        self.text_size.setRange(8, 24)  # 범위 설정
        self.text_size.setValue(14)  # 기본값 14px
        self.text_size.setSuffix("px")
        text_size_control_layout.addWidget(self.text_size)
        text_size_layout.addLayout(text_size_control_layout)
        
        # 텍스트 크기 제한 안내
        text_size_info = QLabel("※ 텍스트 크기 8~24px")
        text_size_info.setStyleSheet(f"color: {STYLES['text_secondary']};")
        text_size_info.setContentsMargins(20, 0, 0, 0)  # 왼쪽 여백 추가
        text_size_layout.addWidget(text_size_info)
        
        group.addWidget(text_size_container)

        # 대화문 색상
        dialog_color_layout = QHBoxLayout()
        dialog_color_layout.addWidget(QLabel("대화문 색상"))
        self.dialog_color = ModernColorButton(STYLES['dialog_color'])
        self.dialog_color.clicked.connect(lambda: self.choose_color("dialog"))
        dialog_color_layout.addWidget(self.dialog_color)
        group.addLayout(dialog_color_layout)
        
        # 나레이션 색상
        narration_color_layout = QHBoxLayout()
        narration_color_layout.addWidget(QLabel("나레이션 색상"))
        self.narration_color = ModernColorButton(STYLES['narration_color'])
        self.narration_color.clicked.connect(lambda: self.choose_color("narration"))
        narration_color_layout.addWidget(self.narration_color)
        group.addLayout(narration_color_layout)

        # 대화문 굵기 설정
        dialog_bold_layout = QHBoxLayout()
        self.dialog_bold = ModernCheckBox("대화문 굵게")
        self.dialog_bold.setChecked(True)
        dialog_bold_layout.addWidget(self.dialog_bold)
        group.addLayout(dialog_bold_layout)
        
        # 전처리 옵션
        preprocess_layout = QVBoxLayout()
        self.remove_asterisk = ModernCheckBox("에스터리스크(*) 제거")
        self.remove_asterisk.setChecked(True)
        preprocess_layout.addWidget(self.remove_asterisk)

        # 말줄임표 자동 변환
        self.convert_ellipsis = ModernCheckBox("말줄임표 자동 변환 (...→…)")
        self.convert_ellipsis.setChecked(True)
        preprocess_layout.addWidget(self.convert_ellipsis)

        group.addLayout(preprocess_layout)
        
        # 초기 들여쓰기 상태 설정
        self.update_indent_state()
        
        return group

    def update_indent_state(self):
        """들여쓰기 설정 상태 업데이트"""
        is_indent_enabled = self.use_text_indent.isChecked()
        self.text_indent.setEnabled(is_indent_enabled)    

    def create_word_replace_settings(self):
        """단어 변경 설정 그룹 생성"""
        group = SettingsGroup("단어 변경")
    
        # 단어 변경 입력 컨테이너
        self.word_replace_container = QWidget()
        self.word_replace_layout = QVBoxLayout(self.word_replace_container)
        self.word_replace_layout.setSpacing(STYLES['spacing_small'])
    
        # 기본 항목 3개 추가
        for _ in range(3):
            self.add_word_replace_entry()
    
        group.addWidget(self.word_replace_container)
    
        # 항목 추가 버튼
        add_btn = ModernButton("+ 항목 추가")
        add_btn.clicked.connect(self.add_word_replace_entry)
        group.addWidget(add_btn)
    
        return group


    def create_asset_settings(self):
        """에셋 관리 설정 그룹 생성"""
        group = SettingsGroup("에셋 관리")
        
        # 스크롤 영역 생성
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(self.get_scrollbar_style())
        
        # 스크롤 영역에 들어갈 위젯 생성
        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setSpacing(STYLES['spacing_small'])
        
        # 캐릭터 카드 업로드 영역
        upload_layout = QHBoxLayout()
        
        self.upload_card_btn = ModernButton("캐릭터 카드 업로드")
        self.upload_card_btn.clicked.connect(self.upload_character_card)
        upload_layout.addWidget(self.upload_card_btn)
        
        self.open_assets_btn = ModernButton("에셋 폴더 열기")
        self.open_assets_btn.clicked.connect(self.open_assets_folder)
        self.open_assets_btn.setEnabled(False)
        upload_layout.addWidget(self.open_assets_btn)
        
        content_layout.addLayout(upload_layout)

        # 여기에 매핑 관리 버튼
        mapping_buttons = self.create_mapping_buttons()
        content_layout.addWidget(mapping_buttons)
        
        # 이미지 URL 매핑 컨테이너
        self.image_url_container = QWidget()
        self.image_url_layout = QVBoxLayout(self.image_url_container)
        self.image_url_layout.setSpacing(STYLES['spacing_small'])
        
        # 기본 항목 추가
        for _ in range(3):
            self.add_image_url_entry()
        
        content_layout.addWidget(self.image_url_container)
        
        # 항목 추가 버튼
        add_btn = ModernButton("+ URL 항목 추가")
        add_btn.clicked.connect(self.add_image_url_entry)
        content_layout.addWidget(add_btn)

        # URL 일괄 입력 버튼 추가
        bulk_input_btn = ModernButton("URL 일괄 입력")
        bulk_input_btn.clicked.connect(lambda: self.create_bulk_url_input_dialog().exec())
        content_layout.addWidget(bulk_input_btn)
        
        # 상태 표시
        self.asset_status = QLabel()
        self.asset_status.setStyleSheet(f"color: {STYLES['text_secondary']};")
        self.asset_status.setWordWrap(True)
        content_layout.addWidget(self.asset_status)
        
        # 스크롤 영역 설정
        scroll.setWidget(scroll_content)
        scroll.setMinimumHeight(200)  # 최소 높이 설정
        scroll.setMaximumHeight(400)  # 최대 높이 설정
        
        # 메인 레이아웃에 스크롤 영역 추가
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll)
        group.content_layout.addLayout(main_layout)
        
        return group

    def extract_url_from_html(self, html_text):
        """HTML 텍스트에서 이미지 URL 추출"""
        try:
            # 이미지 태그에서 URL 추출
            url_match = re.search(r'src=["\'](.*?)["\']', html_text)
            if url_match:
                url = url_match.group(1)
                
                # 프로토콜이 없는 URL 처리
                if url.startswith('//'):
                    url = 'https:' + url
                
                # HTML 엔티티 디코딩
                url = re.sub(r'&amp;', '&', url)
                
                return url.strip()
            return None
        except Exception as e:
            print(f"URL 추출 중 오류 발생: {str(e)}")
            return None

    def save_image_mapping(self, tag, url):
        """이미지 URL 매핑 저장"""
        self.image_cache.mappings[tag] = url
        self.image_cache.save_mappings()

    def load_image_mapping(self, tag):
        """이미지 URL 매핑 불러오기"""
        return self.image_cache.mappings.get(tag)

    def add_image_url_entry(self):
        """이미지 URL 입력 항목 추가"""
        entry = ImageUrlEntry(self.image_url_container)

        # 태그 입력 시 자동으로 캐시된 URL 검색
        def check_cached_url():
            tag = entry.tag_input.text().strip()
            if tag:
                cached_url = self.load_image_mapping(tag)
                if cached_url:
                    entry.url_input.setText(cached_url)
        
        entry.tag_input.editingFinished.connect(check_cached_url)
        
        # URL 입력 시 자동으로 캐시 저장
        def cache_url():
            tag = entry.tag_input.text().strip()
            url = entry.url_input.text().strip()
            if tag and url:
                self.save_image_mapping(tag, url)
        
        entry.url_input.editingFinished.connect(cache_url)
        
        self.image_url_layout.addWidget(entry)
            
        # 레이아웃 업데이트 및 스크롤 영역 조정
        self.image_url_container.adjustSize()
        if hasattr(self, 'asset_status'):
            self.asset_status.setText(
                "사용 방법:\n"
                "1. 이미지 태그에 식별자를 입력하세요 (예: character_happy)\n"
                "2. 해당하는 이미지 URL을 입력하세요\n"
                "3. 본문에서 다음과 같이 사용하세요:\n"
                "   - <img src=\"character_happy\">\n"
                "   - {{img::\"character_happy\"}}\n"
                "   - [img:character_happy]"
            )
        
        # URL 입력 시 자동으로 캐시 저장
        def cache_url():
            tag = entry.tag_input.text().strip()
            url = entry.url_input.text().strip()
            if tag and url:
                self.save_image_mapping(tag, url)
        
        entry.url_input.editingFinished.connect(cache_url)
        
        self.image_url_layout.addWidget(entry)
        
        # 레이아웃 업데이트 및 스크롤 영역 조정
        self.image_url_container.adjustSize()
        if hasattr(self, 'asset_status'):
            self.asset_status.setText("아카라이브 글쓰기에서 이미지 HTML 코드를 이미지 URL에 붙여넣습니다.")

    def upload_character_card(self):
        """캐릭터 카드 업로드 처리"""
        file_filter = "Character Card Files (*.json *.png *.charx);;All Files (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "캐릭터 카드 선택", "", file_filter)
        
        if file_path:
            try:
                print(f"\nProcessing character card: {file_path}")
                if self.card_handler.read_character_card(file_path):
                    if self.card_handler.save_assets():
                        # 디버깅을 위한 정보 출력
                        print("\nAvailable image data:")
                        for key, value in self.card_handler.image_data.items():
                            print(f"- {key}")
                        
                        print("\nImage URI mappings:")
                        for name, uri in self.card_handler.image_uri_map.items():
                            print(f"- {name} -> {uri}")
                        
                        self.open_assets_btn.setEnabled(True)
                        self.update_asset_status(
                            f"캐릭터 카드 로드 완료. {len(self.card_handler.image_data)}개의 이미지가 추출되었습니다."
                        )
                    else:
                        self.update_asset_status("이미지 저장 실패. 로그를 확인하세요.")
                else:
                    self.update_asset_status("캐릭터 카드 로드 실패")
            except Exception as e:
                error_msg = f"오류 발생: {str(e)}"
                print(error_msg)
                self.update_asset_status(error_msg)

    def open_assets_folder(self):
        """에셋 폴더 열기"""
        try:
            if sys.platform == 'win32':
                os.startfile(self.card_handler.assets_folder)
            elif sys.platform == 'darwin':
                os.system(f'open "{self.card_handler.assets_folder}"')
            else:
                os.system(f'xdg-open "{self.card_handler.assets_folder}"')
        except Exception as e:
            self.update_asset_status(f"폴더 열기 실패: {str(e)}")

    def upload_character_card(self):
        """캐릭터 카드 업로드 처리"""
        file_filter = "Character Card Files (*.json *.png *.charx);;All Files (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "캐릭터 카드 선택", "", file_filter)
        
        if file_path:
            try:
                print(f"\nProcessing character card: {file_path}")
                if self.card_handler.read_character_card(file_path):
                    if self.card_handler.save_assets():
                        self.open_assets_btn.setEnabled(True)
                        self.update_asset_status(
                            f"캐릭터 카드 로드 완료. {len(self.card_handler.image_data)}개의 이미지가 추출되었습니다."
                        )
                    else:
                        self.update_asset_status("이미지 저장 실패. 로그를 확인하세요.")
                else:
                    self.update_asset_status("캐릭터 카드 로드 실패")
            except Exception as e:
                error_msg = f"오류 발생: {str(e)}"
                print(error_msg)
                self.update_asset_status(error_msg)

    def open_assets_folder(self):
        """에셋 폴더 열기"""
        try:
            if sys.platform == 'win32':
                os.startfile(self.card_handler.assets_folder)
            elif sys.platform == 'darwin':
                os.system(f'open "{self.card_handler.assets_folder}"')
            else:
                os.system(f'xdg-open "{self.card_handler.assets_folder}"')
        except Exception as e:
            self.update_asset_status(f"폴더 열기 실패: {str(e)}")

    def update_asset_status(self, message):
        """에셋 상태 메시지 업데이트"""
        self.asset_status.setText(message)


    def update_asset_status(self, message):
        """에셋 상태 메시지 업데이트"""
        self.asset_status.setText(message)

    def create_asset_name_img_tag_map(self):
        """이미지 태그 매핑 생성"""
        try:
            img_tags = self.asset_tags_input.toPlainText()
            if not img_tags:
                self.update_asset_status("이미지 태그를 입력해주세요.")
                return
            
            # 입력된 이미지 태그 확인
            print("\nInput image tags:")
            print(img_tags)
            
            img_tag_pattern = re.compile(r'<img[^>]+src="([^"]+)"[^>]*>')
            
            # 에셋 폴더의 파일 목록 가져오기
            asset_files = []
            assets_path = self.card_handler.assets_folder
            if os.path.exists(assets_path):
                print(f"\nChecking assets folder: {assets_path}")
                for filename in os.listdir(assets_path):
                    if filename.lower().endswith(('.png', '.jpg', '.webp')):
                        basename = os.path.splitext(filename)[0]
                        asset_files.append(basename)
                        print(f"Found asset: {basename}")
            
            self.asset_name_img_tag_map.clear()
            matches = list(img_tag_pattern.finditer(img_tags))
            print(f"\nFound {len(matches)} image tags and {len(asset_files)} asset files")
            
            # 매핑 생성
            for asset_name, match in zip(asset_files, matches):
                if match:
                    full_tag = match.group(0)
                    self.asset_name_img_tag_map[asset_name] = full_tag
                    print(f"Created mapping: {asset_name} -> {full_tag}")
            
            self.update_asset_status(
                f"이미지 태그 매핑 완료: {len(self.asset_name_img_tag_map)}개의 이미지가 매핑되었습니다."
            )
            
            # 최종 매핑 결과 출력
            print("\nFinal mapping results:")
            for name, tag in self.asset_name_img_tag_map.items():
                print(f"{name}: {tag}")
            
        except Exception as e:
            error_msg = f"이미지 태그 매핑 실패: {str(e)}"
            print(f"Error: {error_msg}")
            self.update_asset_status(error_msg)


    def create_mapping_buttons(self):
        """매핑 관리 버튼들이 있는 컨테이너 생성"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 매핑 저장 버튼
        save_btn = ModernButton("매핑 저장")
        save_btn.clicked.connect(lambda: self.mapping_manager.save_mapping_set_dialog())
        layout.addWidget(save_btn)
        
        # 매핑 불러오기 버튼
        load_btn = ModernButton("매핑 불러오기")
        load_btn.clicked.connect(lambda: self.mapping_manager.load_mapping_set_dialog())
        layout.addWidget(load_btn)
        
        # 매핑 삭제 버튼
        delete_btn = ModernButton("매핑 삭제")
        delete_btn.clicked.connect(lambda: self.mapping_manager.delete_mapping_set_dialog())
        layout.addWidget(delete_btn)

        return container


    def add_word_replace_entry(self):
        """단어 변경 입력 항목 추가"""
        entry = WordReplaceEntry(self.word_replace_container)
        self.word_replace_layout.addWidget(entry)

    def update_text_size_state(self):
        """텍스트 크기 설정 상태 업데이트"""
        is_text_size_enabled = self.use_text_size.isChecked()
        self.text_size.setEnabled(is_text_size_enabled)        

    def create_io_panel(self):
        """입출력 패널 생성"""
        # 최소 사이즈 힌트 오버라이드를 위한 커스텀 위젯
        class MinSizeWidget(QWidget):
            def minimumSizeHint(self):
                return QSize(0, 0)
            
        panel = MinSizeWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 입력 영역
        input_group = SettingsGroup("텍스트 입력")
        
        rules_label = QLabel(
            "◆ 작성 규칙\n"
            "1. 대화문은 따옴표(\")로 시작하고 끝나야 함\n"
            "2. 빈 줄로 문단 구분"
        )
        rules_label.setStyleSheet(f"color: {STYLES['text_secondary']};")
        input_group.addWidget(rules_label)
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("여기에 텍스트를 입력하세요...")
        input_group.addWidget(self.input_text)
        layout.addWidget(input_group)
        
        # 출력 영역
        output_group = SettingsGroup("변환된 HTML")
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", STYLES['font_size_normal']))
        output_group.addWidget(self.output_text)
        layout.addWidget(output_group)
        
        # 버튼 영역
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(STYLES['spacing_normal'])
        
        convert_btn = ModernButton("HTML 변환", primary=True)
        convert_btn.clicked.connect(self.convert_text)
        button_layout.addWidget(convert_btn)
        
        copy_btn = ModernButton("HTML 복사")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(copy_btn)
        
        layout.addWidget(button_container)
        
        return panel

    def choose_color(self, target):
        """색상 선택 다이얼로그"""
        initial_color = None
        
        if target == "outer_box":
            initial_color = self.outer_box_color.get_color()
        elif target == "inner_box":
            initial_color = self.inner_box_color.get_color()
        elif target == "single_box":
            initial_color = self.single_box_color.get_color()
        if target == "outer_box":
            initial_color = self.outer_box_color.get_color()
        elif target == "inner_box":
            initial_color = self.inner_box_color.get_color()
        elif target == "profile_border":
            initial_color = self.profile_border_color.get_color()
        elif target == "bot_name":
            initial_color = self.bot_name_color.get_color()
        elif target == "dialog":
            initial_color = self.dialog_color.get_color()
        elif target == "narration":
            initial_color = self.narration_color.get_color()
        elif target == "divider_outer":
            initial_color = self.divider_outer_color.get_color()
        elif target == "divider_inner":
            initial_color = self.divider_inner_color.get_color()
        elif target == "divider_solid":
            initial_color = self.divider_solid_color.get_color()
        
        # 향상된 색상 선택 다이얼로그 실행
        color, ok = EnhancedColorDialog.getColor(initial_color, self)
    
        if ok:
            if target == "outer_box":
                self.outer_box_color.setColor(color)
            elif target == "inner_box":
                self.inner_box_color.setColor(color)
            elif target == "single_box":
                self.single_box_color.setColor(color)
                self.inner_box_color.setColor(color)
            if target == "outer_box":
                self.outer_box_color.setColor(color)
            elif target == "inner_box":
                self.inner_box_color.setColor(color)
            elif target == "profile_border":
                self.profile_border_color.setColor(color)
            elif target == "bot_name":
                self.bot_name_color.setColor(color)
            elif target == "dialog":
                self.dialog_color.setColor(color)
            elif target == "narration":
                self.narration_color.setColor(color)
            elif target == "divider_outer":
                self.divider_outer_color.setColor(color)
            elif target == "divider_inner":
                self.divider_inner_color.setColor(color)
            elif target == "divider_solid":
                self.divider_solid_color.setColor(color)

    def choose_tag_color(self, tag_index):
        """태그 색상 선택"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.tag_colors[tag_index].setColor(color.name())

    def toggle_divider_color_settings(self, style):
        """구분선 색상 설정 토글"""
        is_gradient = style == "그라데이션"
        self.gradient_settings.setVisible(is_gradient)
        self.solid_settings.setVisible(not is_gradient)

    def process_image_tags(self, content):
        """이미지 태그 처리 - 다양한 형식 지원"""
        if not content:
            return content

        # URL 매핑 수집
        url_mappings = {}
        for entry in self.image_url_container.findChildren(ImageUrlEntry):
            tag = entry.tag_input.text().strip()
            url = entry.url_input.text().strip()
            if tag and url:
                # 태그에서 식별자만 추출
                tag = self._extract_tag_identifier(tag)
                # URL 정리
                url = self._clean_url(url)
                url_mappings[tag] = url
                print(f"Found mapping: {tag} -> {url}")

        def replace_tag(match):
            """태그를 HTML로 변환"""
            try:
                # 전체 매치 텍스트
                full_match = match.group(0)
                
                # 특수 태그 처리
                if any(tag in full_match.lower() for tag in ['<emotion', '<scene', '<sex']):
                    # 특수 태그에 대한 처리 로직
                    # 예: 특정 스타일이나 클래스를 가진 div로 변환
                    tag_type = ''
                    if 'emotion' in full_match.lower():
                        tag_type = 'emotion'
                    elif 'scene' in full_match.lower():
                        tag_type = 'scene'
                    elif 'sex scene' in full_match.lower():
                        tag_type = 'sex-scene'
                    
                    return f'''
                        <div class="special-tag {tag_type}" style="...">
                            {tag_type.replace('-', ' ').title()}
                        </div>
                    '''
                
                # 기존 이미지 태그 처리 로직
                tag = None
                if '{{' in full_match:
                    if 'img::' in full_match or 'image::' in full_match:
                        tag = full_match.split('::')[1].rstrip('}}').strip('"\'')
                    elif 'img=' in full_match or 'image=' in full_match:
                        tag = full_match.split('=')[1].strip('{}"\' ')
                elif '<img' in full_match or '<image' in full_match:
                    if 'src=' in full_match:
                        tag_match = re.search(r'src=[\'"](.*?)[\'"]', full_match)
                        if tag_match:
                            tag = tag_match.group(1)
                    else:
                        tag_match = re.search(r'=([\'"](.*?)[\'"])', full_match)
                        if tag_match:
                            tag = tag_match.group(2)
                
                if tag and tag in url_mappings:
                    url = url_mappings[tag]
                    return f'''
                        <div style="margin-bottom:1rem; width:100%; text-align:center;">
                            <img style="max-width:100%; border-radius:12px; box-shadow:rgba(0,0,0,0.12) 0px 4px 16px;" 
                                src="{url}" alt="{tag}" class="fr-fic fr-dii">
                        </div>
                    '''
                print(f"Warning: No URL mapping found for image tag: {tag}")
                return full_match
                    
            except Exception as e:
                print(f"Error processing tag {full_match}: {str(e)}")
                return full_match

        # 다양한 이미지 태그 패턴
        patterns = [
            r'\{\{(img|image)::[\'""]*[^}]+[\'""]*\}\}',       # {{img::태그명}}, {{image::태그명}}
            r'\{\{(img|image)=[\'""]*[^}]+[\'""]*\}\}',        # {{img="태그명"}}, {{image="태그명"}}
            r'<(img|image)\s+src=[\'""]*[^\'""]+[\'""]*>',     # <img src="태그명">, <image src="태그명">
            r'<(img|image)=[\'""]*[^>]+[\'""]*>',              # <img="태그명">, <image="태그명">
            r'<emotion=[\'""]*[^>]*[\'""]*>',                  # <emotion="">
            r'<scene=[\'""]*[^>]*[\'""]*>',                    # <scene="">
            r'<sex\s+scene=[\'""]*[^>]*[\'""]*>'              # <sex scene="">
        ]
        
        # 각 패턴에 대해 처리
        result = content
        for pattern in patterns:
            result = re.sub(pattern, replace_tag, result)
        
        return result

    def _extract_tag_identifier(self, tag):
        """이미지 태그에서 식별자만 추출"""
        # img 태그에서 식별자 추출
        if '<img' in tag:
            match = re.search(r'src=[\'"](.*?)[\'"]', tag)
            if match:
                tag = match.group(1)
        
        # {{img::}} 형식에서 식별자 추출
        elif tag.startswith('{{img::'):
            tag = tag.split('::')[1].rstrip('}}').strip('"\'')
        
        # {{img=}} 형식에서 식별자 추출
        elif '{{img=' in tag:
            tag = tag.split('=')[1].strip('{}"\'')
        
        # .png 확장자 제거
        if tag.lower().endswith('.png'):
            tag = tag[:-4]
        
        return tag.strip()

    def _clean_url(self, url):
        """URL 정리"""
        # img 태그에서 URL 추출
        if '<img' in url:
            match = re.search(r'src=[\'"](.*?)[\'"]', url)
            if match:
                url = match.group(1)
        
        # 프로토콜 처리
        if url.startswith('//'):
            url = 'https:' + url
        
        # HTML 엔티티 디코딩
        url = re.sub(r'&amp;', '&', url)
        
        return url.strip()

    def process_image_url(self, url):
        """이미지 URL 처리"""
        if not url or not url.strip():
            print("No URL provided, using default image")
            return DEFAULT_PROFILE_IMAGE
        
        try:
            url = url.strip()
            print(f"Processing URL: {url}")
            
            # HTML 태그에서 URL 추출
            if '<img' in url:
                src_match = re.search(r'src=["\'](.*?)["\']', url)
                if src_match:
                    url = src_match.group(1)
                    print(f"Extracted URL from img tag: {url}")
            
            # 프로토콜 처리
            if url.startswith('//'):
                url = 'https:' + url
                print(f"Added https protocol: {url}")
            
            # 커뮤니티 이미지 URL 처리 (쿼리 파라미터 유지)
            if 'namu.la' in url or 'dcinside.com' in url:
                # 전체 URL을 캡처하도록 패턴 수정
                url_match = re.search(r'((?:https?:)?//[^\s<>"]+?\.(?:jpg|jpeg|png|gif)(?:\?[^"\s<>]*)?)', url)
                if url_match:
                    url = url_match.group(1)
                    if url.startswith('//'):
                        url = 'https:' + url
                    print(f"Processed community URL: {url}")
            
            # HTML 엔티티 디코딩
            url = re.sub(r'&amp;', '&', url)
            
            print(f"Final processed URL: {url}")
            return url

        except Exception as e:
            print(f"Error processing image URL: {str(e)}")
            return DEFAULT_PROFILE_IMAGE

    def update_profile_image(self):
        """프로필 이미지 업데이트"""
        try:
            # 프로필 표시 여부 확인
            if not self.show_profile.isChecked() or not self.show_profile_image.isChecked():
                return
            
            # URL 처리
            image_url = self.process_image_url(self.image_url.text())
            print(f"Using image URL: {image_url}")
            
            # 프레임 스타일에 따른 설정
            frame_style = self.frame_style.currentText()
            width = self.width_input.value()
            height = self.height_input.value()
            
            # 미리보기 업데이트
            self.update_preview()
            
        except Exception as e:
            print(f"Error updating profile image: {str(e)}")

    def init_profile_image_handlers(self):
        """프로필 이미지 관련 핸들러 초기화"""
        # URL 입력 변경 감지
        self.image_url.textChanged.connect(self.update_profile_image)
        
        # 프로필 관련 설정 변경 감지
        self.show_profile.stateChanged.connect(self.update_profile_image)
        self.show_profile_image.stateChanged.connect(self.update_profile_image)
        self.frame_style.currentTextChanged.connect(self.update_profile_image)
        self.width_input.valueChanged.connect(self.update_profile_image)
        self.height_input.valueChanged.connect(self.update_profile_image)

    def get_image_mappings(self):
        """현재 설정된 이미지 매핑 정보 반환"""
        mappings = {}
        for entry in self.image_url_container.findChildren(ImageUrlEntry):
            tag = entry.tag_input.text().strip()
            url = entry.url_input.text().strip()
            if tag and url:
                mappings[tag] = url
        return mappings

    def format_conversation(self, text):
        """대화문 포맷팅"""
        # 기존 코드와 동일
        indent = self.text_indent.value() if self.use_text_indent.isChecked() else 0
        dialog_color = self.dialog_color.get_color()
        narration_color = self.narration_color.get_color()
        dialog_bold = "font-weight:bold;" if self.dialog_bold.isChecked() else ""
        text_size = f"font-size:{self.text_size.value()}px;" if self.use_text_size.isChecked() else ""

        if self.convert_ellipsis.isChecked():
            text = text.replace('...', '…')
        
        # HTML 태그나 스타일 정의를 텍스트로 처리하지 않도록 필터링
        text = re.sub(r'<div\s+style=["\']margin-bottom:1\.5rem;["\']>', '', text)
        text = re.sub(r'</div>', '', text)
        
        # 각 줄을 개별적으로 처리
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            if not line.strip():  # 빈 줄은 브레이크 태그로 변환
                formatted_lines.append('<p><br></p>')
                continue
                
            # HTML 태그로 보이는 텍스트 필터링
            if line.strip().startswith('<') and line.strip().endswith('>'):
                continue
                
            # 대화문 패턴 정의
            pattern = r'(["""\"].*?["""\"])'
            parts = re.split(pattern, line)
            
            line_parts = []
            for part in parts:
                if re.match(pattern, part):
                    # 대화문
                    line_parts.append(
                        f'<span style="color:{dialog_color}; {dialog_bold} {text_size} display:inline-block; text-indent:{indent}px;">{part}</span>'
                    )
                elif part.strip():
                    # 나레이션
                    line_parts.append(
                        f'<span style="color:{narration_color}; {text_size} display:inline-block; text-indent:{indent}px;">{part.strip()}</span>'
                    )
            
            # 각 줄을 하나의 div로 묶음
            if line_parts:
                formatted_lines.append(f'<div style="margin-bottom:1rem;">{"".join(line_parts)}</div>')
        
        return '\n'.join(formatted_lines)

    def create_template(self, content):
        """템플릿 HTML 생성"""
        try:
            # 박스 색상
            box_outer_color = self.outer_box_color.get_color()
            box_inner_color = self.inner_box_color.get_color()
            shadow_value = self.shadow_intensity.value()
        
            if self.show_inner_box.isChecked():
                # 내부 박스가 있을 때
                background_color = box_outer_color  # 외부 박스 색상 사용
                inner_box_style = f"""
                    font-size:{STYLES['font_size_normal']}px;
                    background:{box_inner_color};
                    padding:{STYLES['spacing_large']}px;
                    border-radius:{STYLES['radius_normal']}px;"""
            else:
                # 내부 박스가 없을 때는 내부 박스 색상을 전체 배경색으로 사용
                background_color = box_inner_color  # 내부 박스 색상을 배경색으로 사용
                inner_box_style = f"""
                    font-size:{STYLES['font_size_normal']}px;
                    padding:0;"""
        
            # 프로필 영역 HTML 생성 (프로필 표시 여부에 따라)
            profile_section_html = ''
            if self.show_profile.isChecked():
                try:
                    profile_parts = []
                    
                    # 프로필 이미지
                    if self.show_profile_image.isChecked():
                        profile_border_color = self.profile_border_color.get_color()
                        width = self.width_input.value()
                        height = self.height_input.value()
                        image_url = self.process_image_url(self.image_url.text())
                        
                        if self.frame_style.currentText() == "배너":
                            # 배너 스타일
                            profile_html = f'''
                            <div style="margin-bottom:1rem; width:100%; text-align:center;">
                                <img style="max-width:100%; border-radius:12px;
                                        {f'box-shadow:rgba(0,0,0,0.12) 0px 4px 16px;' if self.show_profile_shadow.isChecked() else ''}" 
                                    src="{image_url}" alt="banner">
                            </div>
                            '''
                        else:
                            # 동그라미 또는 직사각형 스타일
                            if self.frame_style.currentText() == "동그라미":
                                profile_style = f"width:{width}px;height:{width}px;border-radius:50%;"
                            else:  # 직사각형
                                profile_style = f"width:{width}px;height:{height}px;border-radius:8px;object-fit:cover;"
                            
                            profile_html = f'''
                            <div style="margin-bottom:1rem; text-align:center;">
                                <img style="{profile_style}
                                        border:3px solid {profile_border_color};
                                        box-shadow:rgba(0,0,0,0.12) 0px 4px 16px;" 
                                    src="{image_url}" class="fr-fic fr-dii">
                            </div>
                            '''
                        profile_parts.append(profile_html)
                    
                    # 봇 이름
                    if self.show_bot_name.isChecked():
                        bot_name = self.bot_name.text() or "봇 이름"
                        bot_name_color = self.bot_name_color.get_color()
                        bot_name_html = f'''
                            <h3 style="color:{bot_name_color};font-weight:{STYLES['font_weight_bold']};">{bot_name}</h3>
                        '''
                        profile_parts.append(bot_name_html)

                    # 태그 부분 (create_template 메서드 내부)
                    if self.show_tags.isChecked():
                        try:
                            tags_html = []
                            for i in range(len(self.tag_boxes)):
                                if i < len(self.tag_transparent) and self.tag_boxes[i] and self.tag_colors[i]:
                                    # 투명 배경 상태 확인
                                    is_transparent = self.tag_transparent[i].isChecked()
                                    tag_color = self.tag_colors[i].get_color()
                                    tag_text = self.tag_boxes[i].text() or f"태그 {i+1}"
                                    
                                    # 투명 배경일 때와 아닐 때의 스타일 분리
                                    background_style = "transparent" if is_transparent else tag_color
                                    text_color = tag_color if is_transparent else "#FFFFFF"
                                    
                                    tag_html = f'''
                                        <div style="display:inline-block;margin:0.25rem;">
                                            <span style="
                                                background:{background_style};
                                                padding:0.2rem 0.8rem;
                                                border-radius:20px;
                                                font-size:0.85rem;
                                                border:1px solid {tag_color};
                                                color:{text_color};
                                            ">{tag_text}</span>
                                        </div>
                                    '''
                                    tags_html.append(tag_html)
                            
                            if tags_html:
                                tags_container = f'''
                                    <div style="text-align:center;margin:0 auto;max-width:fit-content;">
                                        {''.join(tags_html)}
                                    </div>
                                '''
                                profile_parts.append(tags_container)
                        except Exception as e:
                            print(f"Error creating tags: {str(e)}")
                    
                    # 구분선
                    if self.show_divider.isChecked():
                        thickness = self.divider_thickness.value()  # 굵기 값 가져오기
                        if self.divider_style.currentText() == "그라데이션":
                            divider_outer_color = self.divider_outer_color.get_color()
                            divider_inner_color = self.divider_inner_color.get_color()
                            divider_style = f"background:linear-gradient(to right,{divider_outer_color} 0%,{divider_inner_color} 50%,{divider_outer_color} 100%);"
                        else:
                            solid_color = self.divider_solid_color.get_color()
                            divider_style = f"background:{solid_color};"

                        divider_html = f'''
                            <div style="height:{thickness}px;{divider_style}margin:1rem 0;border-radius:{thickness/2}px;">
                                <br>
                            </div>
                        '''
                        profile_parts.append(divider_html)
                    
                    # 전체 프로필 섹션 조합
                    if profile_parts:
                        profile_section_html = f'''
                            <div style="display:flex;flex-direction:column;text-align:center;margin-bottom:1.25rem;">
                                {''.join(profile_parts)}
                            </div>
                        '''
                    
                except Exception as e:
                    print(f"Error in template creation: {str(e)}")
                    return f"<div>{content}</div>"
            
            template = f'''<p><br></p>
    <p><br></p>
    <div style="font-family:{STYLES['font_family']};
                            color:{STYLES['text']};
                            line-height:1.8;
                            width:100%;
                            max-width:600px;
                            margin:1rem auto;
                            background:{background_color};
                            border-radius:{STYLES['radius_large']}px;
                            box-shadow:0px {shadow_value}px {shadow_value * 2}px rgba(0,0,0,0.2);">
                    <div style="padding:{STYLES['spacing_large']}px;">
                        <div style="{inner_box_style}">
                            {profile_section_html}
                            {content}
                        </div>
                    </div>
                </div>
    <p><br></p>
    <p><br></p>'''
            return template
        except Exception as e:
            print(f"Error in template creation: {str(e)}")
            return f"<div>{content}</div>"

    def convert_text(self):
        """텍스트 변환"""
        try:
            input_text = self.input_text.toPlainText()
            if not input_text.strip():
                self.output_text.setPlainText("")
                return

            # 이미지 태그 처리를 먼저 수행
            content = self.process_image_tags(input_text)
            
            # 단어 변경
            for entry in self.word_replace_container.findChildren(WordReplaceEntry):
                from_word = entry.from_word.text()
                to_word = entry.to_word.text()
                if from_word and to_word:
                    content = content.replace(from_word, to_word)

            # 에스터리스크 제거
            if self.remove_asterisk.isChecked():
                content = re.sub(r'\*+', '', content)

            # 각 문단을 처리
            paragraphs = []
            for paragraph in content.split('\n\n'):
                if paragraph.strip():
                    # 이미 처리된 HTML이면 그대로 사용, 아니면 대화문 포맷팅
                    if paragraph.strip().startswith('<div'):
                        paragraphs.append(paragraph)
                    else:
                        formatted_text = self.format_conversation(paragraph)
                        paragraphs.append(f'<div style="margin-bottom:1.5rem;">{formatted_text}</div>')
            
            # 최종 HTML 생성
            content = '\n'.join(paragraphs)
            template = self.create_template(content)
            
            self.output_text.setPlainText(template)
            
        except Exception as e:
            self.handle_error(f"변환 중 오류가 발생했습니다: {str(e)}")
            print(f"Error details: {e}")

    def copy_to_clipboard(self):
        """HTML 복사"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.output_text.toPlainText())

    def create_bulk_url_input_dialog(self):
        """대량 URL 입력 다이얼로그"""
        dialog = QDialog(self)
        dialog.setWindowTitle("이미지 URL 일괄 입력")
        dialog.setModal(True)  # 모달 대화상자로 설정
        dialog.resize(800, 600)  # 적절한 초기 크기 설정
        
        layout = QVBoxLayout(dialog)
        
        # 스크롤 영역 추가
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(self.get_scrollbar_style())
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 설명 레이블
        instruction = QLabel(
            "웹사이트에서 추출한 이미지 HTML 코드를 순서대로 붙여넣으세요.\n"
            "현재 추출된 이미지 태그:"
        )
        scroll_layout.addWidget(instruction)
        
        # 태그 목록을 스크롤 가능한 텍스트 영역으로 표시
        tag_list = QTextEdit()
        tag_list.setReadOnly(True)
        tag_list.setMaximumHeight(150)  # 태그 목록의 최대 높이 제한
        sorted_tags = sorted(self.card_handler.image_uri_map.keys(), key=str.lower)  # 대소문자 구분 없이 정렬
        tag_list.setText("\n".join(sorted_tags))
        scroll_layout.addWidget(tag_list)
        
        # URL 입력 영역
        url_input = QTextEdit()
        url_input.setPlaceholderText("<img src='...'>\n<img src='...'>\n...")
        url_input.setMinimumHeight(200)  # 최소 높이 설정
        scroll_layout.addWidget(url_input)
        
        # 버튼들을 담을 컨테이너
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        
        # 매핑 생성 버튼
        ok_button = ModernButton("매핑 생성", primary=True)
        ok_button.clicked.connect(lambda: self.process_bulk_mapping_and_close(
            url_input.toPlainText(),
            sorted(list(self.card_handler.image_uri_map.keys()), key=str.lower),  # 대소문자 구분 없이 정렬
            dialog
        ))
        button_layout.addWidget(ok_button)
        
        # 취소 버튼
        cancel_button = ModernButton("취소")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)
        
        scroll_layout.addWidget(button_container)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return dialog

    def process_bulk_mapping_and_close(self, urls_text, image_tags, dialog):
        """URL 매핑 처리 후 다이얼로그 닫기"""
        try:
            success = self.process_bulk_mapping(urls_text, image_tags)
            if success:
                dialog.accept()  # 성공 시에만 다이얼로그 닫기
        except Exception as e:
            QMessageBox.warning(
                self,
                "처리 오류",
                f"매핑 처리 중 오류가 발생했습니다: {str(e)}"
            )

    def process_bulk_mapping(self, urls_text, image_tags):
        """URL과 이미지 태그 매핑 처리"""
        try:
            # URL들을 줄별로 분리하고 HTML에서 URL 추출
            raw_urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
            urls = []
            
            # HTML에서 URL만 추출
            for raw_url in raw_urls:
                if '<img' in raw_url:  # HTML 태그인 경우
                    extracted_url = self.extract_url_from_html(raw_url)
                    if extracted_url:
                        urls.append(extracted_url)
                elif raw_url.startswith('http') or raw_url.startswith('//'): # 직접 URL인 경우
                    urls.append(raw_url)
            
            # 유효한 URL만 필터링
            urls = [url for url in urls if url]
            
            if len(urls) != len(image_tags):
                QMessageBox.warning(
                    self,
                    "매핑 오류",
                    f"URL 수({len(urls)})와 이미지 태그 수({len(image_tags)})가 일치하지 않습니다."
                )
                return False
                
            # 기존 매핑 삭제
            for i in reversed(range(self.image_url_layout.count())):
                self.image_url_layout.itemAt(i).widget().deleteLater()
                
            # 새 매핑 생성
            for tag, url in zip(image_tags, urls):
                entry = ImageUrlEntry(self.image_url_container)
                entry.tag_input.setText(tag)
                
                # URL이 HTML 태그인 경우 추출
                if '<img' in url:
                    url = self.extract_url_from_html(url) or url
                
                entry.url_input.setText(url)
                self.image_url_layout.addWidget(entry)
                
                # 캐시에도 저장
                self.save_image_mapping(tag, url)
                
            QMessageBox.information(
                self,
                "매핑 완료",
                f"{len(image_tags)}개의 매핑이 성공적으로 생성되었습니다."
            )
            return True
                
        except Exception as e:
            QMessageBox.warning(
                self,
                "처리 오류",
                f"매핑 처리 중 오류가 발생했습니다: {str(e)}"
            )
            return False

    def save_all_mappings(self):
        """모든 매핑 저장"""
        mappings = {}
        for i in range(self.image_url_layout.count()):
            entry = self.image_url_layout.itemAt(i).widget()
            tag = entry.tag_input.text().strip()
            url = entry.url_input.text().strip()
            if tag and url:
                mappings[tag] = url
        
        # 파일로 저장
        file_path = QFileDialog.getSaveFileName(
            self,
            "매핑 저장",
            "",
            "JSON 파일 (*.json)"
        )[0]
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(mappings, f, ensure_ascii=False, indent=2)

    def add_mapping_buttons(self):
        """매핑 관리 버튼 추가"""
        button_layout = QHBoxLayout()
        
        bulk_input_btn = ModernButton("일괄 입력")
        bulk_input_btn.clicked.connect(lambda: self.create_bulk_url_input_dialog().exec())
        
        save_btn = ModernButton("매핑 저장")
        save_btn.clicked.connect(self.save_all_mappings)
        
        load_btn = ModernButton("매핑 불러오기")
        load_btn.clicked.connect(self.load_mappings)
        
        button_layout.addWidget(bulk_input_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(load_btn)
        
        return button_layout

    def create_preset_button(self):
        """프리셋 관리 버튼 생성"""
        preset_btn = ModernButton("프리셋 관리")
        preset_btn.setFixedWidth(120)
        preset_btn.clicked.connect(self.show_preset_menu)
        return preset_btn

    def show_preset_menu(self):
        """프리셋 관리 메뉴 표시"""
        menu = QMenu(self)
        
        # 현재 설정 저장
        save_action = menu.addAction("현재 설정을 프리셋으로 저장")
        save_action.triggered.connect(self.preset_manager.save_current_settings)
        
        if self.preset_manager.presets:
            # 저장된 프리셋이 있을 경우 구분선 추가
            menu.addSeparator()
            
            # 저장된 프리셋 메뉴
            load_menu = menu.addMenu("프리셋 불러오기")
            delete_menu = menu.addMenu("프리셋 삭제")
            
            for name in sorted(self.preset_manager.presets.keys()):
                # 불러오기 메뉴
                load_action = load_menu.addAction(name)
                load_action.triggered.connect(lambda checked, n=name: self.preset_manager.load_preset(n))
                
                # 삭제 메뉴
                delete_action = delete_menu.addAction(name)
                delete_action.triggered.connect(lambda checked, n=name: self.preset_manager.delete_preset(n))
        
        # 버튼 위치에 메뉴 표시
        menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))


    def update_profile_style_states(self):
        """프로필 이미지 스타일 설정 상태 업데이트"""
        # 테두리 설정 상태
        is_border_enabled = self.show_profile_border.isChecked()
        self.profile_border_color.setEnabled(is_border_enabled)


    def closeEvent(self, event):
        """프로그램 종료 시 리소스 정리"""
        try:
            # [새로운 부분] 타이머 정리
            if self.preview_timer is not None:
                self.preview_timer.stop()
                self.preview_timer.deleteLater()

            # [기존 기능] 프리셋 저장
            self.preset_manager.save_presets()

            # [새로운 부분] 모든 위젯 정리
            for widget in self.findChildren(QWidget):
                widget.deleteLater()

            # 임시 파일 정리 추가
            if hasattr(self, 'card_handler'):
                self.card_handler.cleanup()
            
            event.accept()
        except Exception as e:
            self.handle_error(f"프로그램 종료 중 오류가 발생했습니다: {str(e)}")
            event.accept()

    def handle_error(self, error_msg):
        """에러 처리 통합 메서드"""
        QMessageBox.warning(self, '오류', error_msg)
        print(f"Error: {error_msg}")  # 로깅용

    def update_preview(self):
        """디바운싱이 적용된 미리보기 업데이트"""
        if hasattr(self, 'input_text') and hasattr(self, 'output_text'):
            # 이전 타이머가 있다면 중지
            if self.preview_timer is not None:
                self.preview_timer.stop()
            
            # 새 타이머 생성
            self.preview_timer = QTimer()
            self.preview_timer.setSingleShot(True)
            self.preview_timer.timeout.connect(self.convert_text)
            self.preview_timer.start(300)  # 300ms 후에 실행

    def export_presets_dialog(self):
        """프리셋 내보내기 다이얼로그"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "프리셋 내보내기", "", 
            "JSON 파일 (*.json);;모든 파일 (*.*)")
        
        if filepath:
            if not filepath.endswith('.json'):
                filepath += '.json'
            self.preset_manager.export_presets(filepath)

    def import_presets_dialog(self):
        """프리셋 가져오기 다이얼로그"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "프리셋 가져오기", "", 
            "JSON 파일 (*.json);;모든 파일 (*.*)")
        
        if filepath:
            self.preset_manager.import_presets(filepath)

    def handle_error(self, error_msg):
        """향상된 에러 처리"""
        # 에러 메시지를 사용자에게 보여주기
        QMessageBox.warning(self, '오류', error_msg)
        # 콘솔에도 출력
        print(f"Error: {error_msg}")
        
        # 심각한 오류인 경우 로그 파일에 기록
        if "심각" in error_msg:
            self.log_error(error_msg)

    def log_error(self, error_msg):
        """에러 로깅"""
        try:
            # 로그 파일 경로 설정
            log_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'error.log')
            
            # 로그 파일에 에러 기록
            with open(log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {error_msg}\n")
        except Exception as e:
            print(f"로그 기록 중 오류 발생: {str(e)}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LogGenerator Pro")
    app.setWindowIcon(QIcon('log_icon.ico'))  # 앱 아이콘 설정
    
    icon_path = resource_path('log_icon.ico')
    app.setWindowIcon(QIcon(icon_path))

    # 애플리케이션 전역 폰트 설정
    font = QFont(STYLES['font_family'], STYLES['font_size_normal'])
    font.setWeight(STYLES['font_weight_normal'])
    app.setFont(font)
    
    # 다크 모드 감지 및 스타일 조정
    if app.styleHints().colorScheme() == Qt.ColorScheme.Dark:
        STYLES.update({
            'background': '#1C1C1E',
            'surface': '#2C2C2E',
            'text': '#FFFFFF',
            'text_secondary': '#98989D',
            'border': '#3A3A3C',
        })
    
    converter = ModernLogGenerator()
    converter.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()       