"""
Макрос предоставляет функционал для создания скрытых (и непечатаемых) слоев
во всех видах чертежа (как правило) или только в текущем активном виде.

По умолчанию скрытые слои создаются с номером 900 и с темно-желтым цветом.

Макрос актуален в случае создания ассоциативных чертежей с проецированием видов
с 3D-модели, когда необходимо убрать какие-то лишние линии
(чаще всего на выносных элементах или разрезах). Один из способ удаления этих
ненужных линий - это перенесение на скрытый и непечатаемый слой.
"""
from .lib_macros.core import *


def dwg_create_hidden_layers(hidden_layer_number = 900, color = 0x999900, do_create_in_all_views: bool = True) -> None:
    """
    Создает скрытые слои с номером `hidden_layer_number` и цветом `color`
    во всех видах (если `do_create_in_all_views == True`) или только в текущем
    активном виде.

    Цвет `color` задается в традиционном формате `0xRRGGBB`.
    """

    def _create_layer(view: KAPI7.IView) -> bool:
        rc = False
        layers: KAPI7.ILayers = view.Layers
        hidden_layer: KAPI7.ILayer = layers.LayerByNumber(hidden_layer_number)
        if hidden_layer is None:
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

    doc: KAPI7.IKompasDocument2D = open_doc2d()

    assert not doc is None

    vlm: KAPI7.IViewsAndLayersManager = doc.ViewsAndLayersManager
    views: KAPI7.IViews = vlm.Views

    if do_create_in_all_views:
        new_layers_count: int = 0
        for i in range(views.Count):
            view: KAPI7.IView = views.View(i)
            new_layers_count += int(_create_layer(view))

        print(f"Общее количество видов: {views.Count}. Созданы скрытые слои в {new_layers_count} видах.")
    else:
        view: KAPI7.IView = views.ActiveView
        is_created = _create_layer(view)
        if is_created:
            print(f"Создан скрытый слой в текущем виде.")
        else:
            print(f"Скрытый слой уже присутствует в текущем виде.")




if __name__ == "__main__":
    dwg_create_hidden_layers(900)

