"""
Макрос предназначен для работы с определенным образом созданными моделями
рукавов высокого давления.

Модели рукавов представляют собой сборку из двух заранее смоделированных
фитингов; сплайна, эскиза окружности и кинематической операции (операции по
траектории), которая моделирует тело рукава.

Макрос предоставляет функционал:
* для изменения диаметра окружности, представляющей собой наружный диаметр РВД,
* для изменения толщины стенки кинематической операции (операции по траектории)
    с этой окружностью.

Макрос актуален для старой версии Компаса без библиотеки "Гибкие шланги".

"""

from .lib_macros.core import *


def set_sketch_circle_diameter(diameter: float) -> None:
    doc, toppart = open_part()

    sketches: list[KAPI7.ISketch] = get_selected(doc, KAPI7.ISketch)

    for sketch in sketches:
        doc2d: KAPI7.IFragmentDocument = sketch.BeginEdit()
        view: KAPI7.IView = doc2d.ViewsAndLayersManager.Views.View(0)
        dc: KAPI7.IDrawingContainer = KAPI7.IDrawingContainer(view)
        circles: list[KAPI7.ICircle] = ensure_list(dc.Objects(2))  #  Окружность
        if len(circles) == 1:
            circles[0].Radius = diameter / 2
            circles[0].Update()
        else:
            print(f"В эскизе '{sketch.Name}' неверное количество окружностей: {len(circles)} (ожидается 1)")

        sketch.EndEdit()


def set_evolution_wall_thickness(thickness: float) -> None:
    assert isinstance(thickness, (float, int))
    doc5, toppart5 = open_part_K5()
    selected = get_selected_K5(doc5)
    for entity in selected:
        if entity.type == LDefin3D.o3d_bossEvolution:
            base_evolution: KAPI5.ksBaseEvolutionDefinition = entity.GetDefinition()
            # base_evolution.SetThinParam(True, 1, thickness, thickness)
            tp: KAPI5.ksThinParam = base_evolution.ThinParam()
            tp.normalThickness = thickness
            tp.reverseThickness = thickness
            tp.thinType = 1
            tp.thin = True  # FIXME не_срабатывает с первого раза. Почему?
            entity.Update()
    doc5.RebuildDocument()



if __name__ == "__main__":

    D = 16
    d = 7.9
    t = (D - d) / 2

    set_sketch_circle_diameter(D)
    set_evolution_wall_thickness(t)
