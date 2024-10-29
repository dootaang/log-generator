import re
import os
import sys  # sys 모듈 추가
import contextlib
import json
import os
from datetime import datetime  # 날짜/시간 처리용
from PyQt6.QtCore import QTimer  # 타이머 기능용
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTextEdit, QLabel, QPushButton,
                           QColorDialog, QLineEdit, QCheckBox, QSpinBox,
                           QTabWidget, QScrollArea, QComboBox, QFrame,
                           QGridLayout, QFileDialog)  # QFileDialog 추가
from PyQt6.QtGui import QFont, QClipboard, QColor, QPalette, QIcon
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QTabWidget
from PyQt6.QtWidgets import (QInputDialog, QMessageBox, QMenu)
from PyQt6.QtCore import QStandardPaths
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtWidgets import QSlider


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

# WordReplaceEntry 클래스 바로 다음에 추가하세요
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
        # 타이머 변수 추가
        self.preview_timer = None
        
        # 아이콘 설정에 resource_path 사용
        icon_path = resource_path('log_icon.ico')
        self.setWindowIcon(QIcon(icon_path))
        
        # 다크모드 변경 감지
        self.color_scheme_handler = QApplication.instance().styleHints()
        self.color_scheme_handler.colorSchemeChanged.connect(self.update_color_scheme)
        
        # 프리셋 매니저 초기화
        self.preset_manager = PresetManager(self)
        
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("LogGenerator Pro")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)  # 최소 창 크기 설정
        self.setup_styles()
    
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(STYLES['spacing_large'], STYLES['spacing_large'], 
                                    STYLES['spacing_large'], STYLES['spacing_large'])
        main_layout.setSpacing(STYLES['spacing_large'])
        
        # === 왼쪽 패널 (설정) ===
        left_panel = self.create_settings_panel()
        main_layout.addWidget(left_panel, 1)
        
        # === 오른쪽 패널 (입출력) ===
        right_panel = self.create_io_panel()
        main_layout.addWidget(right_panel, 2)

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
        panel = QWidget()
        panel.setFixedWidth(400)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(self.get_scrollbar_style())
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(STYLES['spacing_large'])
        
        # === 템플릿 설정 ===
        template_group = self.create_template_settings()
        scroll_layout.addWidget(template_group)
        
        # === 프로필 설정 ===
        profile_group = self.create_profile_settings()
        scroll_layout.addWidget(profile_group)
        
        # === 봇 설정 ===
        bot_group = self.create_bot_settings()
        scroll_layout.addWidget(bot_group)
        
        # === 태그 설정 ===
        tag_group = self.create_tag_settings()
        scroll_layout.addWidget(tag_group)
        
        # === 구분선 설정 ===
        divider_group = self.create_divider_settings()
        scroll_layout.addWidget(divider_group)
        
        # === 텍스트 설정 ===
        text_group = self.create_text_settings()
        scroll_layout.addWidget(text_group)
    
        # === 단어 변경 설정 ===           
        word_replace_group = self.create_word_replace_settings()
        scroll_layout.addWidget(word_replace_group)
    
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
    
        return panel

    def create_template_settings(self):
        """템플릿 설정 그룹 생성"""
        group = SettingsGroup("템플릿 설정")
        
        # 프리셋 관리 버튼 추가 - 여기에 추가
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
    
        # 내부 박스 표시 여부
        inner_box_layout = QHBoxLayout()
        self.show_inner_box = ModernCheckBox("내부 박스 표시")
        self.show_inner_box.setChecked(True)
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
    
        # 그림자 설정
        shadow_layout = QHBoxLayout()
        shadow_layout.addWidget(QLabel("그림자 강도"))
        self.shadow_intensity = ModernSpinBox()
        self.shadow_intensity.setRange(0, 40)
        self.shadow_intensity.setValue(STYLES['shadow_intensity'])
        shadow_layout.addWidget(self.shadow_intensity)
        group.addLayout(shadow_layout)
    
        return group
    
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
        panel = QWidget()
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
        self.input_text.setMinimumHeight(300)
        input_group.addWidget(self.input_text)
        layout.addWidget(input_group)
        
        # 출력 영역
        output_group = SettingsGroup("변환된 HTML")
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(300)
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
        
        # 현재 선택된 색상 가져오기
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

    def process_image_url(self, url):
        """이미지 URL 처리"""
        if not url:
            return DEFAULT_PROFILE_IMAGE
        
        try:
            # URL에서 img 태그 처리
            if '<img' in url:
                src_match = re.search(r'src=["\'](.*?)["\']', url)
                if src_match:
                    url = src_match.group(1)
            
            # URL 프로토콜 처리
            if url.startswith('//'):
                url = 'https:' + url
            
            # 나무위키 이미지 URL 처리
            if 'namu.la' in url:
                url_match = re.search(r'(//.*?\.(png|jpg|jpeg|gif)(\?expires=[^&]+&key=[^&\s]+))', url)
                if url_match:
                    url = 'https:' + url_match.group(1)
                else:
                    url_match = re.search(r'(//.*?\.(png|jpg|jpeg|gif))', url)
                    if url_match:
                        url = 'https:' + url_match.group(1)
            
            return url

        except Exception as e:
            error_msg = f"이미지 URL 처리 중 오류가 발생했습니다: {str(e)}"
            self.handle_error(error_msg)
            return DEFAULT_PROFILE_IMAGE

    def format_conversation(self, text):
        """대화문 포맷팅"""
        indent = self.text_indent.value() if self.use_text_indent.isChecked() else 0
        dialog_color = self.dialog_color.get_color()
        narration_color = self.narration_color.get_color()
        dialog_bold = "font-weight:bold;" if self.dialog_bold.isChecked() else ""
        
        # 텍스트 크기 설정 추가
        text_size = f"font-size:{self.text_size.value()}px;" if self.use_text_size.isChecked() else ""

        # 전처리: 말줄임표 변환
        if self.convert_ellipsis.isChecked():
            text = text.replace('...', '…')
        
        # 대화문 패턴 정의 (모든 종류의 따옴표 인식)
        pattern = r'(["""\"].*?["""\"])'
        parts = re.split(pattern, text)
        
        formatted_parts = []
        for part in parts:
            if re.match(pattern, part):
                # 대화문
                formatted_parts.append(
                    f'<span style="color:{dialog_color}; {dialog_bold} {text_size} display:block; text-indent:{indent}px;">{part}</span>'
                )
            elif part.strip():
                # 나레이션
                formatted_parts.append(
                    f'<span style="color:{narration_color}; {text_size} display:block; text-indent:{indent}px;">{part.strip()}</span>'
                )
        
        return ''.join(formatted_parts)

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
            
            template = f'''
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
            '''
            return template
        except Exception as e:
            print(f"Error in template creation: {str(e)}")
            return f"<div>{content}</div>"

    def convert_text(self):
        try:
            input_text = self.input_text.toPlainText()
            if not input_text.strip():
                self.output_text.setPlainText("")
                return
        
            # 전처리
            if self.remove_asterisk.isChecked():
                input_text = re.sub(r'\*+', '', input_text)
        
            # 단어 변경
            for entry in self.word_replace_container.findChildren(WordReplaceEntry):
                from_word = entry.from_word.text()
                to_word = entry.to_word.text()
                if from_word and to_word:  # 둘 다 비어있지 않은 경우에만 변경
                    input_text = input_text.replace(from_word, to_word)

            # 대화문 처리 및 템플릿 적용
            paragraphs = []
            for paragraph in input_text.strip().split('\n\n'):
                if paragraph.strip():
                    formatted_text = self.format_conversation(paragraph)
                    paragraphs.append(f'<div style="margin-bottom:1.5rem;">{formatted_text}</div>')
            
            content = '\n'.join(paragraphs)
            template = self.create_template(content)
            
            self.output_text.setPlainText(template)
            
        except Exception as e:
            self.handle_error(f"변환 중 오류가 발생했습니다: {str(e)}")  # 새로운 에러 처리 방식 사용

    def copy_to_clipboard(self):
        """HTML 복사"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.output_text.toPlainText())

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

            event.accept()
        except Exception as e:
            # [개선된 부분] 더 자세한 에러 메시지
            error_msg = f"프로그램 종료 중 오류가 발생했습니다: {str(e)}"
            self.handle_error(error_msg)  # 에러 메시지를 사용자에게 보여줌
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