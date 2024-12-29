from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
    QGraphicsEllipseItem, QGraphicsLineItem, QVBoxLayout, QHBoxLayout,
    QToolBar, QAction, QGraphicsTextItem, QInputDialog, QWidget, QGraphicsItem,
    QActionGroup
)
from PyQt5.QtGui import QIcon, QPainter, QPen
from PyQt5.QtCore import Qt, QPointF
from enum import Enum
import csv
from TravelingSalesmanSolver import TravelingSalesmanSolver

class Mode(Enum):
    NODE_SELECTION = 1
    NODE_CREATION = 2
    EDGE_CREATION = 3
    NODE_DELETION = 4

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
        self.connected_edges = []
        self.label = QGraphicsTextItem(name, self)
        self.label.setPos(10, 10)

    def add_edge(self, edge):
        self.connected_edges.append(edge)

    def remove_edges(self):
        for edge in self.connected_edges[:]:
            edge.remove_from_scene()
            other_node = edge.node1 if edge.node2 == self else edge.node2
            other_node.connected_edges.remove(edge)
            self.tsp_app.edges.remove(edge)
        self.connected_edges.clear()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            for edge in self.connected_edges:
                edge.update_position()
        return super().itemChange(change, value)

class Edge(QGraphicsLineItem):
    def __init__(self, node1, node2, weight, scene, parent=None):
        super().__init__(parent)
        self.node1 = node1
        self.node2 = node2
        self.weight = weight
        self.scene = scene
        self.scene.addItem(self)
        self.weight_label = QGraphicsTextItem(str(weight))
        self.scene.addItem(self.weight_label)
        self.node1.add_edge(self)
        self.node2.add_edge(self)
        self.update_position()
        self.highlighted = False
        self.setPen(QPen(Qt.black, 1))

    def set_highlighted(self, highlighted):
   
        self.highlighted = highlighted
        if highlighted:
            self.setPen(QPen(Qt.red, 3))  
        else:
            self.setPen(QPen(Qt.black, 1)) 


    def update_position(self):
        pos1 = self.node1.scenePos()
        pos2 = self.node2.scenePos()
        self.setLine(pos1.x(), pos1.y(), pos2.x(), pos2.y())
        mid_x = (pos1.x() + pos2.x()) / 2
        mid_y = (pos1.y() + pos2.y()) / 2
        self.weight_label.setPos(mid_x, mid_y)

    def remove_from_scene(self):
        self.scene.removeItem(self)
        self.scene.removeItem(self.weight_label)

class TSPApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TSP Solver GUI")
        self.setGeometry(100, 100, 800, 600)
        self.nodes = {}
        self.edges = []
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QHBoxLayout(self.central_widget)
        layout.addWidget(self.view)
        self.mode = Mode.NODE_SELECTION
        self.start_node = None
        self.init_toolbar()

    def init_toolbar(self):
        toolbar = QToolBar(self)
        toolbar.setOrientation(Qt.Vertical)
        self.addToolBar(Qt.LeftToolBarArea, toolbar)

        action_group = QActionGroup(self)
        action_group.setExclusive(True)

        def create_action(icon, mode, tooltip):
            action = QAction(QIcon(icon), tooltip, self)
            action.setCheckable(True)
            action.triggered.connect(lambda: self.set_mode(mode))
            action_group.addAction(action)
            toolbar.addAction(action)
            return action

        create_action("icons/select.png", Mode.NODE_SELECTION, "Select Nodes").setChecked(True)
        create_action("icons/add_node.png", Mode.NODE_CREATION, "Create Nodes")
        create_action("icons/add_edge.png", Mode.EDGE_CREATION, "Create Edges")
        create_action("icons/delete.png", Mode.NODE_DELETION, "Delete Nodes")

        toolbar.addSeparator()

        import_action = QAction(QIcon("icons/import.png"), "Import Graph", self)
        import_action.triggered.connect(self.import_graph)
        toolbar.addAction(import_action)

        export_action = QAction(QIcon("icons/export.png"), "Export Graph", self)
        export_action.triggered.connect(self.export_graph)
        toolbar.addAction(export_action)

        solve_action = QAction(QIcon("icons/solve.png"), "Solve TSP", self)
        solve_action.triggered.connect(self.solve_tsp)
        toolbar.addAction(solve_action)

    def solve_tsp(self):
        if len(self.nodes) < 2:
            print("Not enough nodes to solve the TSP.")
            return

        nodes = {name: node.pos() for name, node in self.nodes.items()}
        edges = [(edge.node1.name, edge.node2.name, edge.weight) for edge in self.edges]

        solver = TravelingSalesmanSolver(nodes, edges)
        result = solver.solve()

        self.clear_highlights()

        if result["solution"] is None:
            print(result["message"])
            self.display_message("No solution exists.")
        else:
            self.highlight_path(result["solution"])

            metrics = (
                f"Best Path: {' -> '.join(result['solution'])}\n"
                f"Cost: {result['cost']}\n"
                f"Iterations: {result['iterations']}\n"
                f"Time Taken: {result['time_taken']:.2f} seconds"
            )
            self.display_message(metrics)

    def highlight_path(self, path):
        """
        Highlight the edges in the solution path.

        Args:
            path (list): List of nodes in the optimal path.
        """
        for i in range(len(path) - 1):
            start_node = path[i]
            end_node = path[i + 1]

            for edge in self.edges:
                if (edge.node1.name == start_node and edge.node2.name == end_node) or \
                (edge.node1.name == end_node and edge.node2.name == start_node):
                    edge.set_highlighted(True)  
                    break

        self.scene.update()

    def clear_highlights(self):

        for edge in self.edges:
            edge.set_highlighted(False)
        self.scene.update()

    def display_message(self, message):

        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "TSP Solution", message)

    def import_graph(self):
        from PyQt5.QtWidgets import QFileDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Import Graph", "", "CSV Files (*.csv);;All Files (*)")
        if file_name:
            self.scene.clear()
            self.nodes.clear()
            self.edges.clear()

            with open(file_name, "r") as file:
                reader = csv.reader(file)
                for row in reader:
                    if row[0] == "NODE":
                        name, x, y = row[1], float(row[2]), float(row[3])
                        self.add_node(QPointF(x, y), name=name)
                    elif row[0] == "EDGE":
                        node1, node2, weight = row[1], row[2], int(row[3])
                        self.create_edge(self.nodes[node1], self.nodes[node2], weight)

    def export_graph(self):
        from PyQt5.QtWidgets import QFileDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Graph", "", "CSV Files (*.csv);;All Files (*)")
        if file_name:
            with open(file_name, "w", newline="") as file:
                writer = csv.writer(file)
                for name, node in self.nodes.items():
                    x, y = node.scenePos().x(), node.scenePos().y()
                    writer.writerow(["NODE", name, x, y])
                for edge in self.edges:
                    writer.writerow(["EDGE", edge.node1.name, edge.node2.name, edge.weight])

    def set_mode(self, mode):
        self.mode = mode
        if mode == Mode.NODE_SELECTION:
            self.enable_node_selection(True)
        else:
            self.enable_node_selection(False)

    def enable_node_selection(self, enable):
        for node in self.nodes.values():
            node.setFlag(QGraphicsEllipseItem.ItemIsMovable, enable)
            node.setFlag(QGraphicsEllipseItem.ItemIsSelectable, enable)

    def mousePressEvent(self, event):
        view_pos = self.view.mapFromGlobal(self.mapToGlobal(event.pos()))
        scene_pos = self.view.mapToScene(view_pos)

        if event.button() == Qt.LeftButton:
            if self.mode == Mode.NODE_CREATION:
                self.add_node(scene_pos)
            elif self.mode == Mode.EDGE_CREATION:
                self.handle_edge_creation(scene_pos)
            elif self.mode == Mode.NODE_DELETION:
                self.handle_node_deletion(scene_pos)

    def add_node(self, pos, name=None):
        if name is None:
            name, ok = QInputDialog.getText(self, "Node Name", "Enter node name:")
            if not ok or not name or name in self.nodes:
                return
        node = DraggableNode(name, self.scene, self)
        node.setPos(pos)
        self.scene.addItem(node)
        self.nodes[name] = node

    

    def handle_edge_creation(self, scene_pos):
        clicked_item = self.scene.itemAt(scene_pos, self.view.transform())
        print(f"Clicked Item: {clicked_item}, Type: {type(clicked_item)}")
        
        while clicked_item and not isinstance(clicked_item, DraggableNode):
            clicked_item = clicked_item.parentItem()

        if isinstance(clicked_item, DraggableNode):
            if not self.start_node:
                self.start_node = clicked_item
                clicked_item.setBrush(Qt.green)  
            else:
                if self.start_node != clicked_item:
                    self.create_edge(self.start_node, clicked_item)
                self.start_node.setBrush(Qt.yellow)
                self.start_node = None
        else:
            if self.start_node:
                self.start_node.setBrush(Qt.yellow) 
            self.start_node = None

    def create_edge(self, node1, node2, weight=None):
        if weight is None:
            weight, ok = QInputDialog.getInt(
                self, "Edge Weight", f"Enter weight for edge {node1.name} - {node2.name}:"
            )
            if not ok:
                return
        edge = Edge(node1, node2, weight, self.scene)
        self.edges.append(edge)

    def handle_node_deletion(self, scene_pos):
        clicked_item = self.scene.itemAt(scene_pos, self.view.transform())
        
        if isinstance(clicked_item, DraggableNode):
            clicked_item.remove_edges()
            self.scene.removeItem(clicked_item)
            del self.nodes[clicked_item.name]
        elif isinstance(clicked_item, Edge):
            clicked_item.node1.connected_edges.remove(clicked_item)
            clicked_item.node2.connected_edges.remove(clicked_item)
            clicked_item.remove_from_scene()
            self.edges.remove(clicked_item)


if __name__ == "__main__":
    app = QApplication([])
    window = TSPApp()
    window.show()
    app.exec_()