from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
    QGraphicsEllipseItem, QGraphicsLineItem, QVBoxLayout, QPushButton, 
    QInputDialog, QGraphicsTextItem, QWidget
)
from PyQt5.QtGui import QPen, QPainter
from PyQt5.QtCore import Qt, QPointF

import sys

class DraggableNode(QGraphicsEllipseItem):
    def __init__(self, x, y, name, scene, parent=None):
        super().__init__(-10, -10, 20, 20, parent)
        self.setBrush(Qt.yellow)
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges, True)
        self.name = name
        self.scene = scene

        # Add label
        self.label = QGraphicsTextItem(name, self)
        self.label.setPos(10, 10)

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.ItemPositionChange:
            # Update edges connected to this node
            for edge in self.scene.edges:
                edge.update_position()
        return super().itemChange(change, value)

class Edge(QGraphicsLineItem):
    def __init__(self, node1, node2, weight, scene, parent=None):
        super().__init__(parent)
        self.node1 = node1
        self.node2 = node2
        self.weight = weight
        self.scene = scene

        # Add weight label
        self.weight_label = QGraphicsTextItem(str(weight), self.scene)
        self.update_position()

    def update_position(self):
        # Update the edge line
        pos1 = self.node1.scenePos()
        pos2 = self.node2.scenePos()
        self.setLine(pos1.x(), pos1.y(), pos2.x(), pos2.y())

        # Update the position of the weight label
        mid_x = (pos1.x() + pos2.x()) / 2
        mid_y = (pos1.y() + pos2.y()) / 2
        self.weight_label.setPos(mid_x, mid_y)

class TSPApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TSP Solver GUI")
        self.setGeometry(100, 100, 800, 600)

        # Graph data
        self.nodes = {}  # {node_name: QGraphicsEllipseItem}
        self.edges = []  # List of Edge objects

        # Scene and View
        self.scene = QGraphicsScene()
        self.scene.edges = self.edges
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)

        # UI Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)
        layout.addWidget(self.view)

        # Buttons
        self.add_node_button = QPushButton("Add Node")
        self.add_node_button.clicked.connect(self.add_node_mode)
        layout.addWidget(self.add_node_button)

        self.add_edge_button = QPushButton("Add Edge")
        self.add_edge_button.clicked.connect(self.add_edge_mode)
        layout.addWidget(self.add_edge_button)

        self.clear_button = QPushButton("Clear Canvas")
        self.clear_button.clicked.connect(self.clear_canvas)
        layout.addWidget(self.clear_button)

        # State
        self.adding_node = False
        self.adding_edge = False
        self.selected_nodes = []

    def add_node_mode(self):
        self.adding_node = True
        self.adding_edge = False

    def add_edge_mode(self):
        self.adding_node = False
        self.adding_edge = True

    def clear_canvas(self):
        self.scene.clear()
        self.nodes.clear()
        self.edges.clear()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.view.mapToScene(event.pos())
            if self.adding_node:
                self.add_node(pos)
            elif self.adding_edge:
                self.select_node_for_edge(pos)

    def add_node(self, pos):
        name, ok = QInputDialog.getText(self, "Node Name", "Enter node name:")
        if ok and name and name not in self.nodes:
            node = DraggableNode(pos.x(), pos.y(), name, self.scene)
            node.setPos(pos)
            self.scene.addItem(node)
            self.nodes[name] = node

    def select_node_for_edge(self, pos):
        for node_name, node_item in self.nodes.items():
            node_pos = node_item.scenePos()
            if abs(pos.x() - node_pos.x()) < 15 and abs(pos.y() - node_pos.y()) < 15:
                self.selected_nodes.append(node_item)
                if len(self.selected_nodes) == 2:
                    self.create_edge()
                break

    def create_edge(self):
        node1, node2 = self.selected_nodes
        weight, ok = QInputDialog.getInt(self, "Edge Weight", f"Enter weight for edge {node1.name} - {node2.name}:")
        if ok:
            edge = Edge(node1, node2, weight, self.scene)
            self.scene.addItem(edge)
            self.edges.append(edge)
        self.selected_nodes.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TSPApp()
    window.show()
    sys.exit(app.exec_())