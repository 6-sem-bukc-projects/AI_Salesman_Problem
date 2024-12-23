from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
    QGraphicsEllipseItem, QGraphicsLineItem, QVBoxLayout, QHBoxLayout,
    QToolBar, QAction, QGraphicsTextItem, QInputDialog, QWidget, QGraphicsItem,
    QActionGroup
)
from PyQt5.QtGui import QIcon, QPainter
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
        """Remove all edges connected to this node."""
        for edge in self.connected_edges[:]:
            # Remove the edge from the scene
            edge.remove_from_scene()
            # Remove the edge from the other connected node
            other_node = edge.node1 if edge.node2 == self else edge.node2
            other_node.connected_edges.remove(edge)
            # Remove the edge from the TSP app's edge list
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

    def update_position(self):
        pos1 = self.node1.scenePos()
        pos2 = self.node2.scenePos()
        self.setLine(pos1.x(), pos1.y(), pos2.x(), pos2.y())
        mid_x = (pos1.x() + pos2.x()) / 2
        mid_y = (pos1.y() + pos2.y()) / 2
        self.weight_label.setPos(mid_x, mid_y)

    def remove_from_scene(self):
        """Removes the edge and its label from the scene."""
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

        # Add separator
        toolbar.addSeparator()

        # Import/Export Actions
        import_action = QAction(QIcon("icons/import.png"), "Import Graph", self)
        import_action.triggered.connect(self.import_graph)
        toolbar.addAction(import_action)

        export_action = QAction(QIcon("icons/export.png"), "Export Graph", self)
        export_action.triggered.connect(self.export_graph)
        toolbar.addAction(export_action)

        # Solve 
        solve_action = QAction(QIcon("icons/solve.png"), "Solve TSP", self)
        solve_action.triggered.connect(self.solve_tsp)
        toolbar.addAction(solve_action)

    def solve_tsp(self):
        if len(self.nodes) <= 2:
            print("Not enough nodes to solve the TSP.")
            return

        # Extract node positions and edges for the solver
        nodes = {name: node.pos() for name, node in self.nodes.items()}
        edges = [(edge.node1.name, edge.node2.name, edge.weight) for edge in self.edges]

        # Solve TSP using ACO
        solver = TravelingSalesmanSolver(nodes, edges)
        result = solver.solve()

        # Display the result
        if result["solution"] is None:
            print(result["message"])
        else:
            print(f"Best Path: {result['solution']}")
            print(f"Best Cost: {result['cost']}")
            print(f"Iterations: {result['iterations']}")
            print(f"Time Taken: {result['time_taken']:.2f} seconds")

    def import_graph(self):
        """Import graph from a CSV file."""
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
        """Export graph to a CSV file."""
        from PyQt5.QtWidgets import QFileDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Graph", "", "CSV Files (*.csv);;All Files (*)")
        if file_name:
            with open(file_name, "w", newline="") as file:
                writer = csv.writer(file)
                # Write nodes
                for name, node in self.nodes.items():
                    x, y = node.scenePos().x(), node.scenePos().y()
                    writer.writerow(["NODE", name, x, y])
                # Write edges
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
        # Map the event position to the view's coordinates
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
        # Detect the item at the clicked position
        clicked_item = self.scene.itemAt(scene_pos, self.view.transform())
        print(f"Clicked Item: {clicked_item}, Type: {type(clicked_item)}")
        
        # Traverse up the hierarchy to check for a DraggableNode
        while clicked_item and not isinstance(clicked_item, DraggableNode):
            clicked_item = clicked_item.parentItem()

        if isinstance(clicked_item, DraggableNode):
            # If no start node is set, set the clicked node as start_node
            if not self.start_node:
                self.start_node = clicked_item
                clicked_item.setBrush(Qt.green)  # Highlight the selected node
            else:
                # If start_node is already set, create edge if nodes are distinct
                if self.start_node != clicked_item:
                    self.create_edge(self.start_node, clicked_item)
                # Reset the start_node (even if clicked on the same node)
                self.start_node.setBrush(Qt.yellow)  # Reset original color
                self.start_node = None
        else:
            # If clicked outside any node, reset start_node
            if self.start_node:
                self.start_node.setBrush(Qt.yellow)  # Reset original color
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
        # Detect the item at the clicked position
        clicked_item = self.scene.itemAt(scene_pos, self.view.transform())
        
        if isinstance(clicked_item, DraggableNode):
            # If it's a node, remove the node and its connected edges
            clicked_item.remove_edges()
            self.scene.removeItem(clicked_item)
            del self.nodes[clicked_item.name]
        elif isinstance(clicked_item, Edge):
            # If it's an edge, remove it cleanly (edge + label)
            clicked_item.node1.connected_edges.remove(clicked_item)
            clicked_item.node2.connected_edges.remove(clicked_item)
            clicked_item.remove_from_scene()
            self.edges.remove(clicked_item)


if __name__ == "__main__":
    app = QApplication([])
    window = TSPApp()
    window.show()
    app.exec_()