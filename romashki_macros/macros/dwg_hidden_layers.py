"""
Макрос предоставляет функционал для создания скрытых слоев, как правило,
во всех видах чертежа.

По умолчанию скрытые слои создаются с номером 900 и с темно-желтым цветом.

"""
from .lib_macros.core import *


def dwg_create_hidden_layers(hidden_layer_number = 900, color = 0x999900, do_create_everywhere = True) -> None:
    def create_layer(view: KAPI7.IView) -> bool:
        rc = False
        layers: KAPI7.ILayers = view.Layers
        hidden_layer: KAPI7.ILayer = layers.LayerByNumber(hidden_layer_number)
        if hidden_layer == None:
            current_layer_number: int = view.LayerNumber

            hidden_layer = layers.Add()
            hidden_layer.Name = "Скрытое"
            hidden_layer.Color = color_traditional_to_kompas(color)
            hidden_layer.LayerNumber = hidden_layer_number
            hidden_layer.Update()

            view.LayerNumber = current_layer_number
            view.Update()

            rc = True

        hidden_layer.Visible = False
        hidden_layer.Printable = False
        hidden_layer.Update()

        view.Update()
        return rc

    iKompasObject5, iKompasObject7 = get_kompas_objects()
    app: KAPI7.IApplication = get_app7(iKompasObject7)
    doc: KAPI7.IKompasDocument2D = KAPI7.IKompasDocument2D(app.ActiveDocument)

    assert not doc is None

    vlm: KAPI7.IViewsAndLayersManager = doc.ViewsAndLayersManager
    views: KAPI7.IViews = vlm.Views

    new_layers_count: int = 0
    i: int = 0

    if do_create_everywhere:
        for do in views:
            do: KAPI7.IDrawingObject
            view: KAPI7.IView = KAPI7.IView(do)

            i += int(create_layer(view))

        print(f"Общее количество видов: {i}. Созданы скрытые слои в {new_layers_count} видах.")
    else:
        view: KAPI7.IView = views.ActiveView
        is_created = create_layer(view)
        if is_created:
            print(f"Создан скрытый слой в текущем виде.")
        else:
            print(f"Скрытый слой уже присутствует в текущем виде.")




if __name__ == "__main__":
    dwg_create_hidden_layers(900)

