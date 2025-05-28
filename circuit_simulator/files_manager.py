import json
import os
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QPointF

class FilesManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.component_classes_map = main_window.get_component_classes_map()

    def new_file(self):
        if self._maybe_save():
            self.main_window._clear_scene() 
            self.main_window.current_file_path = None
            self.main_window._set_modified(False)
            self.main_window.statusBar().showMessage("已创建新文档")
            print("成功新建文档")

    def open_file(self):
        if self._maybe_save():
            filePath, _ = QFileDialog.getOpenFileName(
                self.main_window, "打开电路文件", "",
                "电路文件 (*.circuit);;所有文件 (*.*)"
            )
            if filePath:
                self._perform_load(filePath)

    def save_file(self):
        if self.main_window.current_file_path:
            return self._perform_save(self.main_window.current_file_path)
        else:
            return self.save_file_as()

    def save_file_as(self):
        suggested_filename = os.path.basename(self.main_window.current_file_path) if self.main_window.current_file_path else "未命名.circuit"
        save_dir = os.path.dirname(self.main_window.current_file_path) if self.main_window.current_file_path else ""

        filePath, _ = QFileDialog.getSaveFileName(
            self.main_window, "保存电路文件",
            os.path.join(save_dir, suggested_filename),
            "电路文件 (*.circuit);;所有文件 (*.*)"
        )
        if filePath:
            if not filePath.endswith(".circuit") and not "." in os.path.basename(filePath):
                filePath += ".circuit"
            return self._perform_save(filePath)
        return False

    def _maybe_save(self): # 询问用户是否要保存
        if not self.main_window.is_modified:
            return True
        ret = QMessageBox.warning(
            self.main_window, "电路模拟器",
            "文档已被修改。\n你想保存你的更改吗?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
        )
        if ret == QMessageBox.Save:
            return self.save_file()
        elif ret == QMessageBox.Cancel:
            return False
        return True # 不保存并继续当前的操作

    def _perform_save(self, filePath):
        try:
            data = {"components": [], "wires": []}
            scene = self.main_window.scene
            GraphicComponentItemBase = self.component_classes_map.get('GraphicComponentItem')

            if not GraphicComponentItemBase:
                QMessageBox.critical(self.main_window, "保存错误", "基本元件类 'GraphicComponentItem' 未在映射中定义。")
                return False

            for item in scene.components:
                if isinstance(item, GraphicComponentItemBase):
                    comp_data = {
                        "name": item.name,
                        "spice_type": item.spice_type,
                        "pos": {"x": item.pos().x(), "y": item.pos().y()},
                        "rotation": item.rotation(),
                        "params": item.params.copy()
                    }
                    comp_data["pins_nodes"] = {pin_key: pin.node_name for pin_key, pin in item.pins.items()}
                    data["components"].append(comp_data)

            for wire in scene.wires:
                if wire.start_pin and wire.end_pin:
                    start_comp = wire.start_pin.parentItem()
                    end_comp = wire.end_pin.parentItem()
                    
                    if not (isinstance(start_comp, GraphicComponentItemBase) and isinstance(end_comp, GraphicComponentItemBase)):
                        continue

                    start_pin_key = next((key for key, val in start_comp.pins.items() if val == wire.start_pin), None)
                    end_pin_key = next((key for key, val in end_comp.pins.items() if val == wire.end_pin), None)

                    if start_pin_key and end_pin_key:
                        wire_data = {
                            "start_comp_name": start_comp.name,
                            "start_pin_key": start_pin_key,
                            "end_comp_name": end_comp.name,
                            "end_pin_key": end_pin_key,
                            "path_points": [{"x": p.x(), "y": p.y()} for p in wire.path_points] if hasattr(wire, 'path_points') else []
                        }
                        data["wires"].append(wire_data)
            
            with open(filePath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            
            self.main_window.current_file_path = filePath
            self.main_window._set_modified(False)
            self.main_window.statusBar().showMessage(f"文件已保存到 {os.path.basename(filePath)}")
            print(f"成功保存文档: {filePath}")
            return True
        except Exception as e:
            QMessageBox.critical(self.main_window, "保存错误", f"保存文件失败: {str(e)}")
            print(f"保存文档失败: {str(e)}")
            return False

    def _perform_load(self, filePath):
        try:
            with open(filePath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.main_window._clear_scene()
            scene = self.main_window.scene
            
            components_map = {} 

            for comp_data in data.get("components", []):
                spice_type_str = comp_data["spice_type"]
                name = comp_data["name"]
                pos_data = comp_data["pos"]
                rotation = comp_data.get("rotation", 0)
                saved_params = comp_data.get("params", {})

                item = None
                CompClass = self.component_classes_map.get(spice_type_str)

                if CompClass:
                    item = CompClass(name)
                else:
                    QMessageBox.warning(self.main_window, "加载警告", f"加载 '{name}' ({spice_type_str}) 失败：未知元件类型 '{spice_type_str}'。")
                    continue 

                if item:
                    item.setPos(QPointF(pos_data["x"], pos_data["y"]))
                    item.setRotation(rotation)
                    item.params.update(saved_params)
                    
                    pins_nodes_data = comp_data.get("pins_nodes", {})
                    for pin_key, node_name in pins_nodes_data.items():
                        if pin_key in item.pins:
                            item.pins[pin_key].node_name = node_name

                    scene.addItem(item)
                    
                    if item not in scene.components: # 确保它在列表中
                         scene.components.append(item)
                    components_map[name] = item
            
            WireItemClass = self.component_classes_map.get('WireItem')
            if WireItemClass:
                for wire_data in data.get("wires", []):
                    start_comp_name = wire_data["start_comp_name"]
                    start_pin_key = wire_data["start_pin_key"]
                    end_comp_name = wire_data["end_comp_name"]
                    end_pin_key = wire_data["end_pin_key"]
                    
                    start_comp = components_map.get(start_comp_name)
                    end_comp = components_map.get(end_comp_name)

                    if start_comp and end_comp:
                        start_pin = start_comp.pins.get(start_pin_key)
                        end_pin = end_comp.pins.get(end_pin_key)
                        if start_pin and end_pin:
                            wire = WireItemClass(start_pin, end_pin)
                            path_points_data = wire_data.get("path_points", [])
                            if hasattr(wire, 'path_points') and path_points_data:
                                 wire.path_points = [QPointF(p["x"], p["y"]) for p in path_points_data]
                                 if hasattr(wire, 'update_path'):
                                     wire.update_path()
                            
                            scene.addItem(wire)
                            if wire not in scene.wires: # 确保它在列表中
                                scene.wires.append(wire)
            
            self.main_window.current_file_path = filePath
            self.main_window._set_modified(False)
            self.main_window.statusBar().showMessage(f"文件 {os.path.basename(filePath)} 已加载")
            print(f"成功打开文档: {filePath}")

        except Exception as e:
            QMessageBox.critical(self.main_window, "打开错误", f"打开文件失败: {str(e)}")
            print(f"打开文档失败: {str(e)}")