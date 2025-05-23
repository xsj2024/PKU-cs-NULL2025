from PySpice.Spice.Netlist import Circuit

def validate_connections(scene):
    # 检查电压源是否形成回路
    for comp in scene.components:
        if comp.spice_type == "V":
            connected_pins = set()
            for wire in scene.wires:
                if wire.start_pin in comp.pins:
                    connected_pins.add(wire.start_pin)
                if wire.end_pin in comp.pins:
                    connected_pins.add(wire.end_pin)
            if len(connected_pins) < 2:
                raise ValueError(f"电压源 {comp.name} 未形成闭合回路！")
            

def generate_spice_netlist(scene):
    circuit = Circuit('Custom Circuit')
    node_counter = 0
    node_map = {}
    
    # 第一遍：为所有引脚分配临时唯一ID（用于连通性分析）
    pin_groups = []
    all_pins = set()
    gnd_pins = set()
    
    # 收集所有连线关系
    for wire in scene.wires:
        pin_groups.append({wire.start_pin, wire.end_pin})
        all_pins.update([wire.start_pin, wire.end_pin])
        
    # 合并连通组（同一导线上的引脚应属于同一组）
    merged = True
    while merged:
        merged = False
        for i in range(len(pin_groups)):
            for j in range(i+1, len(pin_groups)):
                if pin_groups[i] & pin_groups[j]:  # 有交集
                    pin_groups[i] |= pin_groups[j]  # 合并
                    del pin_groups[j]
                    merged = True
                    break
            if merged:
                break
    
    # 为每个连通组分配节点名
    for group in pin_groups:
        node_name = f'n{node_counter}'
        node_counter += 1
        for pin in group:
            node_map[pin] = node_name

    # 处理接地引脚
    for comp in scene.components:
        if comp.spice_type == "GND":
            for pin_item in comp.pins.values():
                # 强制覆盖该引脚对应的节点为0
                node_map[pin_item] = '0'
            
                # 同时确保连通性分析中该引脚所在组也映射到0
                for group in pin_groups:
                    if pin_item in group:
                        for p in group:
                            node_map[p] = '0'

    # 添加元件到SPICE电路
    for comp in scene.components:
        if comp.spice_type == 'R':
            if hasattr(comp, 'value'):
                circuit.R(comp.name, 
                         node_map[comp.pins['left']], 
                         node_map[comp.pins['right']], 
                         comp.value)  # 假设元件有value属性
            else:
                # 默认值为1kΩ
                circuit.R(comp.name, 
                         node_map[comp.pins['left']], 
                         node_map[comp.pins['right']], 
                         1e3)
        elif comp.spice_type == 'V':
            if hasattr(comp, 'value'):
                circuit.V(comp.name, 
                         node_map[comp.pins['plus']], 
                         node_map[comp.pins['minus']], 
                         comp.value)
            else:
                # 默认值为5V
                circuit.V(comp.name, 
                         node_map[comp.pins['plus']], 
                         node_map[comp.pins['minus']], 
                         5)
        elif comp.spice_type == 'D':
            # 若二极管有参数值
            if hasattr(comp, "value"):
                circuit.model(comp.name, 'D', IS=comp.value)
            else:
                # 默认值为1e-14
                circuit.model(comp.name, 'D', IS=1e-14)
            circuit.D(comp.name,
                     node_map[comp.pins['anode']], 
                     node_map[comp.pins['cathode']], 
                     model=comp.name)
    #validate_connections(scene)  # 验证连接
    # 在pin中维护节点对应的spice节点名称
    for pin in all_pins:
        if pin in node_map:
            node_name = node_map[pin]
            # 例如将节点名称存储在元件中
            pin.node_name = node_name
        else:
            print(f"Warning: Pin {pin} has no corresponding node name.")
    return circuit