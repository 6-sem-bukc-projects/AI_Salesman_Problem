from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
    QGraphicsEllipseItem, QGraphicsLineItem, QVBoxLayout, QPushButton,
    QInputDialog, QGraphicsTextItem, QWidget, QGraphicsItem
)
from PyQt5.QtGui import QPen, QPainter
from PyQt5.QtCore import Qt, QPointF

import csv
from PyQt5.QtWidgets import QFileDialog


class DraggableNode(QGraphicsEllipseItem):
    def __init__(self, name, scene, tsp_app, parent=None):
        super().__init__(-10, -10, 20, 20, parent)
        self.setBrush(Qt.yellow)
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges, True)
        self.name = name
        self.scene = scene
        self.tsp_app = tsp_app

        # Store connected edges
        self.connected_edges = []

        # Add label
        self.label = QGraphicsTextItem(name, self)
        self.label.setPos(10, 10)

    def add_edge(self, edge):
        """Add an edge to the node's connections."""
        self.connected_edges.append(edge)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            # Notify all connected edges to update their positions
            for edge in self.connected_edges:
                edge.update_position()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            # Notify TSPApp about the right-click on this node
            self.tsp_app.handle_node_right_click(self)
        super().mousePressEvent(event)

class Edge(QGraphicsLineItem):
    def __init__(self, node1, node2, weight, scene, parent=None):
        super().__init__(parent)
        self.node1 = node1
        self.node2 = node2
        self.weight = weight
        self.scene = scene

        # Add the edge to the scene
        self.scene.addItem(self)

        # Add weight label
        self.weight_label = QGraphicsTextItem(str(weight))
        self.scene.addItem(self.weight_label)

        # Register this edge with the nodes
        self.node1.add_edge(self)
        self.node2.add_edge(self)

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

        self.clear_button = QPushButton("Clear Canvas")
        self.clear_button.clicked.connect(self.clear_canvas)
        layout.addWidget(self.clear_button)

        self.export_button = QPushButton("Export Graph")
        self.export_button.clicked.connect(self.export_graph)
        layout.addWidget(self.export_button)

        self.import_button = QPushButton("Import Graph")
        self.import_button.clicked.connect(self.import_graph)
        layout.addWidget(self.import_button)

        # State
        self.adding_node = False
        self.start_node = None

    def add_node_mode(self):
        self.adding_node = True

    def clear_canvas(self):
        self.scene.clear()
        self.nodes.clear()
        self.edges.clear()
        self.start_node = None

    def mousePressEvent(self, event):
        pos = self.view.mapToScene(event.pos())
        if event.button() == Qt.LeftButton and self.adding_node:
            self.add_node(pos)

    def add_node(self, pos):
        name, ok = QInputDialog.getText(self, "Node Name", "Enter node name:")
        if ok and name and name not in self.nodes:
            node = DraggableNode(name, self.scene, self)
            node.setPos(pos)
            self.scene.addItem(node)
            self.nodes[name] = node

    def handle_node_right_click(self, clicked_node):
        if not self.start_node:
            # Start edge creation
            self.start_node = clicked_node
        elif self.start_node != clicked_node:
            # Finish edge creation
            self.create_edge(self.start_node, clicked_node)
            self.start_node = None  # Reset start node after creating edge
        else:
            # Reset edge creation if clicked on the same node
            self.start_node = None

    def create_edge(self, node1, node2):
        weight, ok = QInputDialog.getInt(self, "Edge Weight", f"Enter weight for edge {node1.name} - {node2.name}:")
        if ok:
            # Create the edge
            edge = Edge(node1, node2, weight, self.scene)
            self.scene.addItem(edge)
            self.edges.append(edge)
            # Register the edge with both nodes
            node1.add_edge(edge)
            node2.add_edge(edge)

    def export_graph(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Graph", "", "CSV Files (*.csv)")
        if file_path:
            # Ensure the file has the .csv extension
            if not file_path.endswith(".csv"):
                file_path += ".csv"
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Node1", "Node2", "Weight"])
                for edge in self.edges:
                    writer.writerow([edge.node1.name, edge.node2.name, edge.weight])
            print(f"Graph exported to {file_path}")

    def import_graph(self):
        # Clear the canvas before importing
        self.clear_canvas()

        file_path, _ = QFileDialog.getOpenFileName(self, "Import Graph", "", "CSV Files (*.csv)")
        if file_path:
            with open(file_path, mode='r') as file:
                reader = csv.reader(file)
                header = next(reader)  # Skip the header row
                node_positions = {}
                for row in reader:
                    node1_name, node2_name, weight = row

                    # Create or retrieve node1
                    if node1_name not in self.nodes:
                        node1 = self.add_node_with_position(node1_name, node_positions)
                    else:
                        node1 = self.nodes[node1_name]

                    # Create or retrieve node2
                    if node2_name not in self.nodes:
                        node2 = self.add_node_with_position(node2_name, node_positions)
                    else:
                        node2 = self.nodes[node2_name]

                    # Create edge with weight
                    self.create_edge_from_import(node1, node2, int(weight))

            print(f"Graph imported from {file_path}")

    def add_node_with_position(self, name, node_positions):
        # Check if node has already been given a position
        if name not in node_positions:
            # Generate a unique position for the node
            pos = self.scene.sceneRect().center()  # Start at the center
            offset_x = len(node_positions) * 50  # Offset by 50 units per node
            pos = pos + QPointF(offset_x, offset_x)
            node_positions[name] = pos

        # Create the node
        pos = node_positions[name]
        node = DraggableNode(name, self.scene, self)
        node.setPos(pos)
        self.scene.addItem(node)
        self.nodes[name] = node
        return node

    def create_edge_from_import(self, node1, node2, weight):
        # Directly create the edge without prompting for weight
        edge = Edge(node1, node2, weight, self.scene)
        self.scene.addItem(edge)
        self.edges.append(edge)
        node1.add_edge(edge)
        node2.add_edge(edge)

if __name__ == "__main__":
    app = QApplication([])
    window = TSPApp()
    window.show()
    app.exec_()