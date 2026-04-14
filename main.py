#!/usr/bin/env python3
"""
WikiTableQuestions Dataset Annotation Tool (PyQt5 version)
Allows users to view questions and tables, select relevant rows, and save annotations.
"""

import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                             QTableWidget, QTableWidgetItem, QMessageBox,
                             QFileDialog, QHeaderView, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from datasets import load_dataset


class WikiTableAnnotator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WikiTableQuestions Annotator")
        self.setGeometry(100, 100, 1200, 800)
        
        # Data
        self.dataset = None
        self.current_index = 0
        self.annotations = {}
        self.notes = {}  # Store notes per instance
        self.selected_rows = set()
        self.annotation_file = "annotations.json"
        self.notes_file = "notes.json"
        self.current_answers = []  # Store current instance answers for highlighting
        
        # Load existing annotations
        self.load_annotations()
        self.load_notes()
        
        # Create UI
        self.init_ui()
        
        # Load dataset
        self.load_dataset()
        
    def init_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Top control bar
        control_layout = QHBoxLayout()
        
        self.instance_label = QLabel("0/0")
        self.instance_label.setFont(QFont('Arial', 10, QFont.Bold))
        control_layout.addWidget(QLabel("Instance:"))
        control_layout.addWidget(self.instance_label)
        control_layout.addSpacing(10)
        
        self.prev_btn = QPushButton("← Previous")
        self.prev_btn.clicked.connect(self.prev_instance)
        control_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("Next →")
        self.next_btn.clicked.connect(self.next_instance)
        control_layout.addWidget(self.next_btn)
        
        control_layout.addSpacing(20)
        
        save_btn = QPushButton("Save Annotations")
        save_btn.clicked.connect(self.save_annotations)
        control_layout.addWidget(save_btn)
        
        export_btn = QPushButton("Export JSON")
        export_btn.clicked.connect(self.export_annotations)
        control_layout.addWidget(export_btn)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # Question section
        question_label = QLabel("Question:")
        question_label.setFont(QFont('Arial', 10, QFont.Bold))
        main_layout.addWidget(question_label)
        
        self.question_text = QTextEdit()
        self.question_text.setMaximumHeight(80)
        self.question_text.setReadOnly(True)
        self.question_text.setFont(QFont('Arial', 11))
        main_layout.addWidget(self.question_text)
        
        # Answer section
        answer_label = QLabel("Answer:")
        answer_label.setFont(QFont('Arial', 10, QFont.Bold))
        answer_label.setStyleSheet("color: green;")
        main_layout.addWidget(answer_label)
        
        self.answer_text = QTextEdit()
        self.answer_text.setMaximumHeight(60)
        self.answer_text.setReadOnly(True)
        self.answer_text.setFont(QFont('Arial', 11))
        self.answer_text.setStyleSheet("background-color: #f0fff0; color: #006400;")
        main_layout.addWidget(self.answer_text)
        
        # ID section
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("ID:"))
        self.id_label = QLabel("")
        self.id_label.setFont(QFont('Arial', 9))
        id_layout.addWidget(self.id_label)
        id_layout.addStretch()
        main_layout.addLayout(id_layout)
        
        # Instructions
        instructions = QLabel("Click on rows to select/deselect them as relevant. Selected rows are highlighted in blue.")
        instructions.setStyleSheet("color: blue; font-style: italic;")
        main_layout.addWidget(instructions)
        
        # Table section
        table_label = QLabel("Table:")
        table_label.setFont(QFont('Arial', 10, QFont.Bold))
        main_layout.addWidget(table_label)
        
        self.table_widget = QTableWidget()
        self.table_widget.setSelectionMode(QTableWidget.MultiSelection)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.cellClicked.connect(self.on_cell_clicked)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_widget.verticalHeader().setVisible(True)
        main_layout.addWidget(self.table_widget)
        
        # Selected rows info
        self.selected_label = QLabel("Selected rows: 0")
        self.selected_label.setFont(QFont('Arial', 10))
        main_layout.addWidget(self.selected_label)
        
        # Notes section
        notes_label = QLabel("Notes (optional):")
        notes_label.setFont(QFont('Arial', 10, QFont.Bold))
        main_layout.addWidget(notes_label)
        
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(80)
        self.notes_text.setPlaceholderText("Add any notes or comments about this instance...")
        self.notes_text.setFont(QFont('Arial', 10))
        self.notes_text.textChanged.connect(self.on_notes_changed)
        main_layout.addWidget(self.notes_text)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
    def load_dataset(self):
        self.status_bar.showMessage("Loading dataset from Hugging Face...")
        QApplication.processEvents()  # Update UI
        
        try:
            self.dataset = load_dataset("wikitablequestions", split="train")
            self.status_bar.showMessage(f"Loaded {len(self.dataset)} instances")
            self.display_instance()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load dataset: {str(e)}")
            self.status_bar.showMessage("Error loading dataset")
            
    def display_instance(self):
        if self.dataset is None or len(self.dataset) == 0:
            return
            
        instance = self.dataset[self.current_index]
        
        # Update instance counter
        self.instance_label.setText(f"{self.current_index + 1}/{len(self.dataset)}")
        
        # Display question
        self.question_text.setPlainText(instance['question'])
        
        # Display answer (handle both list and string formats)
        answers = instance.get('answers', [])
        if isinstance(answers, list) and len(answers) > 0:
            # Join multiple answers with commas
            answer_text = ', '.join(str(a) for a in answers)
            self.current_answers = [str(a).strip().lower() for a in answers]
        else:
            answer_text = str(answers) if answers else "No answer available"
            self.current_answers = [str(answers).strip().lower()] if answers else []
        self.answer_text.setPlainText(answer_text)
        
        # Display ID
        instance_id = instance.get('id', f"instance_{self.current_index}")
        self.id_label.setText(instance_id)
        
        # Get table data
        table = instance['table']
        headers = table['header']
        rows = table['rows']
        
        # Setup table
        self.table_widget.clear()
        self.table_widget.setRowCount(len(rows))
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)
        
        # Populate table
        for i, row in enumerate(rows):
            for j, cell in enumerate(row):
                item = QTableWidgetItem(str(cell))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                item.setForeground(QColor(0, 0, 0))  # Black text for visibility
                
                # Subtle highlight if cell contains an answer (not invasive)
                cell_str = str(cell).strip().lower()
                if self.current_answers and cell_str in self.current_answers:
                    # Very subtle yellow tint - barely noticeable
                    item.setBackground(QColor(255, 255, 220))  # Very light yellow
                
                self.table_widget.setItem(i, j, item)
        
        # Resize columns to content
        self.table_widget.resizeColumnsToContents()
        
        # Load previously selected rows for this instance
        instance_id = instance.get('id', f"instance_{self.current_index}")
        self.selected_rows = set(self.annotations.get(instance_id, []))
        
        # Load notes for this instance
        note_text = self.notes.get(instance_id, "")
        self.notes_text.blockSignals(True)  # Prevent triggering textChanged
        self.notes_text.setPlainText(note_text)
        self.notes_text.blockSignals(False)
        
        # Apply selection highlighting
        self.update_row_highlighting()
        self.update_selected_label()
        
    def on_cell_clicked(self, row, column):
        # Toggle row selection
        if row in self.selected_rows:
            self.selected_rows.remove(row)
        else:
            self.selected_rows.add(row)
            
        self.update_row_highlighting()
        self.update_selected_label()
        
        # Auto-save annotation
        self.save_current_annotation()
    
    def on_notes_changed(self):
        # Auto-save notes when changed
        self.save_current_notes()
        
    def update_row_highlighting(self):
        # Clear all highlighting first
        for i in range(self.table_widget.rowCount()):
            for j in range(self.table_widget.columnCount()):
                item = self.table_widget.item(i, j)
                if item:
                    # Check if this cell contains an answer
                    cell_str = item.text().strip().lower()
                    has_answer = self.current_answers and cell_str in self.current_answers
                    
                    # Default: white background, or subtle yellow if it has an answer
                    if has_answer:
                        item.setBackground(QColor(255, 255, 220))  # Very light yellow
                    else:
                        item.setBackground(QColor(255, 255, 255))  # White background
                    item.setForeground(QColor(0, 0, 0))  # Black text
        
        # Highlight selected rows (this overrides answer highlighting)
        for row in self.selected_rows:
            for j in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, j)
                if item:
                    item.setBackground(QColor(173, 216, 230))  # Light blue background
                    item.setForeground(QColor(0, 0, 0))  # Black text
                    
    def update_selected_label(self):
        selected_list = sorted(list(self.selected_rows))
        self.selected_label.setText(f"Selected rows: {len(selected_list)} → {selected_list}")
        
    def save_current_annotation(self):
        if self.dataset is None:
            return
            
        instance = self.dataset[self.current_index]
        instance_id = instance.get('id', f"instance_{self.current_index}")
        
        # Save selected rows for this instance
        self.annotations[instance_id] = sorted(list(self.selected_rows))
    
    def save_current_notes(self):
        if self.dataset is None:
            return
            
        instance = self.dataset[self.current_index]
        instance_id = instance.get('id', f"instance_{self.current_index}")
        
        # Save notes for this instance (only if non-empty)
        note_text = self.notes_text.toPlainText().strip()
        if note_text:
            self.notes[instance_id] = note_text
        elif instance_id in self.notes:
            # Remove empty notes
            del self.notes[instance_id]
        
    def next_instance(self):
        if self.dataset is None:
            return
            
        self.save_current_annotation()
        self.save_current_notes()
        
        if self.current_index < len(self.dataset) - 1:
            self.current_index += 1
            self.display_instance()
        else:
            QMessageBox.information(self, "Info", "This is the last instance.")
            
    def prev_instance(self):
        if self.dataset is None:
            return
            
        self.save_current_annotation()
        self.save_current_notes()
        
        if self.current_index > 0:
            self.current_index -= 1
            self.display_instance()
        else:
            QMessageBox.information(self, "Info", "This is the first instance.")
            
    def save_annotations(self):
        self.save_current_annotation()
        self.save_current_notes()
        
        try:
            with open(self.annotation_file, 'w') as f:
                json.dump(self.annotations, f)
            with open(self.notes_file, 'w') as f:
                json.dump(self.notes, f)
            self.status_bar.showMessage(f"Saved {len(self.annotations)} annotations and {len(self.notes)} notes")
            QMessageBox.information(self, "Success", f"Annotations and notes saved!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")
            
    def load_annotations(self):
        if os.path.exists(self.annotation_file):
            try:
                with open(self.annotation_file, 'r') as f:
                    self.annotations = json.load(f)
                print(f"Loaded {len(self.annotations)} existing annotations")
            except Exception as e:
                print(f"Failed to load annotations: {str(e)}")
    
    def load_notes(self):
        if os.path.exists(self.notes_file):
            try:
                with open(self.notes_file, 'r') as f:
                    self.notes = json.load(f)
                print(f"Loaded {len(self.notes)} existing notes")
            except Exception as e:
                print(f"Failed to load notes: {str(e)}")
                
    def export_annotations(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Annotations",
            "annotations.json",
            "JSON Files (*.json);;All Files (*)"
        )
        if filename:
            try:
                # Export both annotations and notes in a combined file
                export_data = {
                    "annotations": self.annotations,
                    "notes": self.notes
                }
                with open(filename, 'w') as f:
                    json.dump(export_data, f)
                QMessageBox.information(self, "Success", f"Annotations and notes exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
                
    def closeEvent(self, event):
        # Auto-save on close
        self.save_current_annotation()
        self.save_current_notes()
        try:
            with open(self.annotation_file, 'w') as f:
                json.dump(self.annotations, f)
            with open(self.notes_file, 'w') as f:
                json.dump(self.notes, f)
        except:
            pass
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = WikiTableAnnotator()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()