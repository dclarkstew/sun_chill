def heat_sink_design(panel_SA, num_bars):

    # Constant
    density_aluminum = 2700 # kg/m^3

    # Inputs
    bar_length = 0.982 # meters
    bar_width = 0.003175 # meters # 1/8 in
    bar_height = 0.0254 # meters # 1 in

    # Calcs
    bar_volume = bar_length * bar_width * bar_height
    bar_SArea = (bar_length * bar_height) * 2 + bar_length * bar_width
    bar_SArea_covering_panel = bar_length * bar_width

    # Num bars
    total_bar_volume = bar_volume * num_bars
    total_bar_SArea = bar_SArea * num_bars
    total_bar_SArea_covering_panel = bar_SArea_covering_panel * num_bars

    # Outputs
    panel_dissipate_SArea = panel_SA - total_bar_SArea_covering_panel
    heatsink_dissipate_SArea = total_bar_SArea
    total_bar_weight = total_bar_volume * density_aluminum


    return panel_dissipate_SArea, heatsink_dissipate_SArea, total_bar_weight



