"""
Модуль предоставляет классы для виджетов, которые используются, как правило,
в графических интерфейсах для настроек отдельных макросов.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.resources import get_resource_path

from src import math_utils


EXT_PART = "Компас-Деталь (*.m3d)"
EXT_ASSEMBLY = "Компас-Сборка (*.a3d)"
EXT_ALL = "Все файлы (*)"


def move_to_screen_center(widget: QtWidgets.QWidget) -> None:
    screen = QtWidgets.qApp.primaryScreen()
    if screen is None:
        raise Exception("Cannot find primary screen")
    s_size = screen.size()
    widget.move(
        int(s_size.width() / 2 - widget.width() / 2),
        int(s_size.height() / 2 - widget.height() / 2)
    )

def get_icon_from_color(color: int, size: int = 16) -> QtGui.QIcon:
    p = QtGui.QPixmap(size, size)
    painter = QtGui.QPainter(p)
    painter.setBrush(QtGui.QColor(color))
    painter.setPen(QtGui.QColorConstants.Black)
    painter.drawRect(0, 0, size - 1, size - 1)
    painter.end()
    return QtGui.QIcon(p)

def get_monospace_font() -> QtGui.QFont:
    font = QtGui.QFont()
    font.setFamilies(["Liberation Mono", "Consolas", "Courier New", "monospace"])
    font.setStyleHint(QtGui.QFont.StyleHint.Monospace)
    return font


class LabelImage(QtWidgets.QLabel):
    def __init__(self, path: str, parent = None):
        super().__init__(parent)
        self._pixmap = QtGui.QPixmap(path)
        self.setPixmap(self._pixmap)

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        p = self._pixmap.scaled(self.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)

        painter = QtGui.QPainter(self)
        painter.translate(self.width()/2 - p.width()/2, self.height()/2 - p.height()/2)
        painter.drawPixmap(0, 0, p)

    def move_to_screen_center(self) -> None:
        s_size = QtWidgets.qApp.primaryScreen().size()
        self.move(
            int(s_size.width() / 2 - self.width() / 2),
            int(s_size.height() / 2 - self.height() / 2)
        )


class WidgetColorSelect(QtWidgets.QWidget):
    color_changed = QtCore.pyqtSignal(int)

    def __init__(self, color: int = 0xffffff, parent = None) -> None:
        super().__init__()
        self.color: int = 0

        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

        self.setMinimumSize(16, 16)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        self.set_color(color)

    def set_color(self, new_color: int) -> None:
        if new_color < 0:
            new_color = 0
        if new_color > 0xffffff:
            new_color = 0xffffff
        self.color: int = new_color
        self.update()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._pressed = True
            event.accept()
            return

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton \
                and self._pressed \
                and QtCore.QRect(QtCore.QPoint(0, 0), self.size()).contains(event.pos()):
            self.show_dialog()
            event.accept()

        self._pressed = False

    def show_dialog(self) -> None:
        color: int = QtWidgets.QColorDialog.getColor(
            QtGui.QColor(self.color),
            self.parent()
        )

        if color.isValid():
            rgb = color.rgb() & 0xffffff
            self.set_color(rgb)
            self.color_changed.emit(rgb)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)

        brush_style = QtCore.Qt.BrushStyle.SolidPattern if self.isEnabled() else QtCore.Qt.BrushStyle.DiagCrossPattern
        pen_style = QtCore.Qt.PenStyle.DashLine if self.hasFocus() else QtCore.Qt.PenStyle.SolidLine
        border_color = QtWidgets.qApp.palette().mid().color()

        brush = QtGui.QBrush(QtGui.QColor(self.color), brush_style)
        pen = QtGui.QPen(border_color, 1, pen_style)
        painter.setPen(pen)

        painter.fillRect(1, 1, self.width() - 2, self.height() - 2, brush)

        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)



class WidgetGradientColorSelect(QtWidgets.QWidget):
    color_changed = QtCore.pyqtSignal(list)

    def __init__(self, color1: int = 0xffffff, color2: int = 0x000000, parent = None) -> None:
        super().__init__(parent)

        self.cs1 = WidgetColorSelect(color1)
        self.cs1.color_changed.connect(lambda c: self._emit_color_changed_signal())
        self.cs2 = WidgetColorSelect(color2)
        self.cs2.color_changed.connect(lambda c: self._emit_color_changed_signal())

        self.btn_remove_gradient = QtWidgets.QPushButton("Убрать градиент")
        self.btn_remove_gradient.setToolTip("Сделать второй цвет таким же, как и первый")
        self.btn_remove_gradient.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum,
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        self.btn_remove_gradient.clicked.connect(self.remove_gradient)

        self._layout = QtWidgets.QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)
        self._layout.addWidget(self.cs1)
        self._layout.addWidget(self.cs2)
        self._layout.addWidget(self.btn_remove_gradient)
        self.setLayout(self._layout)

    def remove_gradient(self) -> None:
        self.cs2.set_color(self.cs1.color)
        self._emit_color_changed_signal()

    def _emit_color_changed_signal(self) -> None:
        self.color_changed.emit([self.cs1.color, self.cs2.color])

    def set_color(self, color: tuple[int, int]) -> None:
        c1, c2 = color
        self.cs1.set_color(c1)
        self.cs2.set_color(c2)

    def get_color(self) -> tuple[int,int]:
        return (self.cs1.color, self.cs2.color)


class GradientColorDelegate(QtWidgets.QStyledItemDelegate):
    ITEM_ROLE_GRADIENT_COLOR = 0x0101

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

    def createEditor(
            self,
            parent: QtWidgets.QWidget,
            option: QtWidgets.QStyleOptionViewItem,
            index: QtCore.QModelIndex
            ) -> QtWidgets.QWidget:
        editor = WidgetGradientColorSelect(parent=parent)
        editor.setAutoFillBackground(True)
        return editor

    def sizeHint(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> QtCore.QSize:
        return QtCore.QSize(100, 32)

    def setEditorData(self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex) -> None:
        color: tuple[int, int] = index.data(GradientColorDelegate.ITEM_ROLE_GRADIENT_COLOR)
        editor.set_color(color)

    def setModelData(self, editor: QtWidgets.QWidget, model: QtCore.QAbstractItemModel, index: QtCore.QModelIndex) -> None:
        color: tuple[int, int] = editor.get_color()
        model.setData(index, color, GradientColorDelegate.ITEM_ROLE_GRADIENT_COLOR)

    def updateEditorGeometry(self, editor: QtWidgets.QWidget, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        editor.setGeometry(option.rect);

    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        super().paint(painter, option, index)

        color: tuple[int, int] = index.data(GradientColorDelegate.ITEM_ROLE_GRADIENT_COLOR)
        c1, c2 = color

        g = QtGui.QLinearGradient(option.rect.topLeft(), option.rect.topRight())
        g.setColorAt(0, QtGui.QColor(c1))
        g.setColorAt(1, QtGui.QColor(c2))

        border_color = QtWidgets.qApp.palette().mid().color()

        painter.setBrush(g)
        painter.setPen(QtGui.QPen(border_color, 1))

        spacingX = 5
        spacingY = 5
        painter.drawRect(option.rect.adjusted(0, 0, -1, -1).adjusted(spacingX, spacingY, -spacingX, -spacingY))


class ColorsListView(QtWidgets.QListView):
    data_changed = QtCore.pyqtSignal(list)

    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        self.setSpacing(2)

        self._delegate = GradientColorDelegate()
        self.setItemDelegate(self._delegate)

        self._model = QtGui.QStandardItemModel()
        self.setModel(self._model)

        self._model.dataChanged.connect(lambda a, b, c: self.data_changed.emit(self.get_colors()))

    def set_colors(self, colors: list[tuple[int, int]]) -> None:
        for c in colors:
            self.add_color(c)

    def get_colors(self) -> list[tuple[int,int]]:
        l = []
        for i in range(self._model.rowCount()):
            c = self._model.index(i, 0).data(GradientColorDelegate.ITEM_ROLE_GRADIENT_COLOR)
            l.append(c)
        return l

    def add_color(self, color: tuple[int,int] = [0xffffff, 0x000000]) -> None:
        item = QtGui.QStandardItem()
        item.setData(color, GradientColorDelegate.ITEM_ROLE_GRADIENT_COLOR)
        self._model.appendRow(item)

    def remove_color(self, row: int) -> None:
        self._model.removeRow(row)

    def remove_selected(self) -> None:
        selected: list[QtCore.QModelIndex] = self.selectedIndexes()
        if len(selected) == 0:
            return
        index = selected[0]
        self.remove_color(index.row())


class LineEditDelegate(QtWidgets.QStyledItemDelegate):
    ROLE_OLD_VALUE = 0x0101

    item_renamed = QtCore.pyqtSignal(QtCore.QModelIndex, str, str)  # old, new

    def createEditor(
            self,
            parent: QtWidgets.QWidget,
            option: QtWidgets.QStyleOptionViewItem,
            index: QtCore.QModelIndex
            ) -> QtWidgets.QWidget:
        editor = QtWidgets.QLineEdit(parent)
        editor.setFrame(False)
        index.model().setData(index, index.data(), self.ROLE_OLD_VALUE)
        return editor

    def setEditorData(self, editor: QtWidgets.QLineEdit, index: QtCore.QModelIndex) -> None:
        value = index.model().data(index, QtCore.Qt.ItemDataRole.EditRole)
        editor.setText(value)

    def setModelData(self, editor: QtWidgets.QLineEdit, model: QtCore.QAbstractItemModel, index: QtCore.QModelIndex) -> None:
        value = editor.text()
        model.setData(index, value, QtCore.Qt.EditRole)
        self.item_renamed.emit(index, index.data(self.ROLE_OLD_VALUE), value)

    def updateEditorGeometry(self, editor: QtWidgets.QWidget, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        editor.setGeometry(option.rect)


class StringListSelector(QtWidgets.QWidget):

    list_changed = QtCore.pyqtSignal()
    selection_changed = QtCore.pyqtSignal(list)

    # QtCore.pyqtSignal(QtGui.QStandardItem) почему-то отказывается принимать, поэтому здесь указаны object
    item_renamed = QtCore.pyqtSignal(object, str)  # old, new
    item_added = QtCore.pyqtSignal(object)
    item_deleted = QtCore.pyqtSignal(object)


    def __init__(self, create_new_item_func = lambda: QtGui.QStandardItem("элемент"), parent = None) -> None:
        super().__init__(parent)

        self._create_new_item_func = create_new_item_func

        self._is_ordering_allowed = True
        self._is_duplicating_allowed = True
        self._is_adding_allowed = True
        self._is_name_editing_allowed = True
        self._is_deleting_allowed = True
        self._is_multiple_selecting_allowed = True

        self._model = QtGui.QStandardItemModel()
        self._model.dataChanged.connect(lambda: self.list_changed.emit())

        self._delegate = LineEditDelegate()
        self._delegate.item_renamed.connect(self._item_renamed)

        self._view = QtWidgets.QListView()
        self._view.setModel(self._model)
        self._view.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self._view.selectionModel().selectionChanged.connect(self._selection_changed)
        self._view.setItemDelegate(self._delegate)

        self._btn_up = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/arrow_up.svg")), "")
        self._btn_up.setToolTip("Переместить выбранное выше")
        self._btn_up.clicked.connect(lambda: self.move_selected_in_order(True))

        self._btn_down = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/arrow_down.svg")), "")
        self._btn_down.setToolTip("Переместить выбранное ниже")
        self._btn_down.clicked.connect(lambda: self.move_selected_in_order(False))

        self._btn_add = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/add.svg")), "")
        self._btn_add.setToolTip("Добавить")
        self._btn_add.clicked.connect(lambda: self.add_new_item(self._create_new_item_func()))

        self._btn_duplicate = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/copy.svg")), "")
        self._btn_duplicate.setToolTip("Дублировать выбранное")
        self._btn_duplicate.clicked.connect(self.duplicate_selected)

        self._btn_delete = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/delete.svg")), "")
        self._btn_delete.setToolTip("Удалить выбранное")
        self._btn_delete.clicked.connect(self.delete_selected)


        self._layout_btns = QtWidgets.QHBoxLayout()
        self._layout_btns.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self._layout_btns.setSpacing(2)
        self._layout_btns.addWidget(self._btn_up)
        self._layout_btns.addWidget(self._btn_down)
        self._layout_btns.addWidget(self._btn_add)
        self._layout_btns.addWidget(self._btn_duplicate)
        self._layout_btns.addWidget(self._btn_delete)

        self._layout_main = QtWidgets.QVBoxLayout()
        self._layout_main.addWidget(self._view)
        self._layout_main.addLayout(self._layout_btns)
        self._layout_main.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout_main)

    def set_ordering_allowed(self, is_ordering_allowed: bool) -> None:
        self._is_ordering_allowed = is_ordering_allowed
        self._btn_up.setVisible(self._is_ordering_allowed)
        self._btn_down.setVisible(self._is_ordering_allowed)

    def set_adding_allowed(self, is_adding_allowed: bool) -> None:
        self._is_adding_allowed = is_adding_allowed
        self._btn_add.setVisible(self._is_adding_allowed)

    def set_duplicating_allowed(self, is_duplicating_allowed: bool) -> None:
        self._is_duplicating_allowed = is_duplicating_allowed
        self._btn_duplicate.setVisible(self._is_duplicating_allowed)

    def set_deleting_allowed(self, is_deleting_allowed: bool) -> None:
        self._is_deleting_allowed = is_deleting_allowed
        self._btn_delete.setVisible(self._is_deleting_allowed)

    def set_name_editing_allowed(self, is_editing_allowed: bool) -> None:
        self._is_name_editing_allowed = is_editing_allowed
        if self._is_name_editing_allowed:
            self._view.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked)
        else:
            self._view.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

    def set_read_only(self) -> None:
        self.set_ordering_allowed(False)
        self.set_adding_allowed(False)
        self.set_duplicating_allowed(False)
        self.set_deleting_allowed(False)
        self.set_name_editing_allowed(False)

    def get_list(self) -> list[str]:
        l: list[str] = []
        for r in range(self._model.rowCount()):
            l.append(self._model.index(r, 0).data())
        return l

    def move_selected_in_order(self, do_move_up: bool) -> None:
        selected: list[QtCore.QModelIndex] = self._view.selectedIndexes()
        if len(selected) == 0:
            return

        selected_row_indexes: list[int] = sorted([i.row() for i in selected])

        if (selected_row_indexes[0] > 0 and do_move_up) \
                or (selected_row_indexes[-1] <= self._model.rowCount() - 2 and not do_move_up):
            root = QtCore.QModelIndex()

            _range = selected_row_indexes if do_move_up else reversed(selected_row_indexes)

            for r in _range:
                r2 = r + (-1 if do_move_up else +1)
                item = QtGui.QStandardItem(self._model.item(r, 0))
                self._model.removeRow(r)
                self._model.insertRow(r2, item)

            self._view.selectionModel().clear()
            for r in selected_row_indexes:
                r2 = r + (-1 if do_move_up else +1)
                self._view.selectionModel().select(
                    self._model.index(r2, 0),
                    QtCore.QItemSelectionModel.SelectionFlag.Select
                )

            self.list_changed.emit()

    def add_new_item(self, item: QtGui.QStandardItem, is_silent: bool = False, do_not_switch_selection: bool = False) -> None:
        self._model.appendRow(item)

        if not is_silent:
            self.item_added.emit(item)
            self.list_changed.emit()

        if not do_not_switch_selection:
            self._view.selectionModel().clear()
            self._view.selectionModel().select(
                self._model.index(self._model.rowCount() - 1, 0),
                QtCore.QItemSelectionModel.SelectionFlag.Select
            )

    def delete_selected(self) -> None:
        selected: list[QtCore.QModelIndex] = self._view.selectedIndexes()
        if len(selected) == 0:
            return

        root = QtCore.QModelIndex()

        selected_row_indexes = sorted([i.row() for i in selected])

        deleted_count = 0
        for r in selected_row_indexes:
            item = self._model.item(r, 0)
            self._model.removeRow(r - deleted_count, root)
            self.item_deleted.emit(item)
            deleted_count += 1

        if len(selected_row_indexes) == 1:
            r = min(r, self._model.rowCount() - 1)
            self._view.selectionModel().select(
                self._model.index(r, 0),
                QtCore.QItemSelectionModel.SelectionFlag.Select
            )
        self.list_changed.emit()

    def duplicate_selected(self) -> None:
        selected: list[QtCore.QModelIndex] = self._view.selectedIndexes()
        if len(selected) == 0:
            return

        selected_row_indexes = sorted([i.row() for i in selected])

        self._view.selectionModel().clear()

        duplicated_count = 0
        for r in selected_row_indexes:
            r2 = r + duplicated_count + 1

            new_item = QtGui.QStandardItem(self._model.item(r + duplicated_count, 0))
            self._model.insertRow(r2, new_item)
            self.item_added.emit(new_item)

            duplicated_count += 1

            self._view.selectionModel().select(
                self._model.index(r2, 0),
                QtCore.QItemSelectionModel.SelectionFlag.Select
            )
        self.list_changed.emit()

    def clear_items(self, is_silent: bool = True) -> None:
        self._model.clear()
        if not is_silent:
            self.list_changed.emit()

    def _selection_changed(self) -> None:
        self.selection_changed.emit(self.get_selected())

    def _item_renamed(self, index: QtCore.QModelIndex, old: str, new: str) -> None:
        item = self._model.item(index.row(), index.column())
        self.item_renamed.emit(item, new)
        self.list_changed.emit()

    def get_selected(self) -> list[QtGui.QStandardItem]:
        rows = sorted([i.row() for i in self._view.selectedIndexes()])
        return [self._model.item(r, 0) for r in rows]

    def get_one_selected_item(self) -> QtGui.QStandardItem|None:
        items = self.get_selected()
        if len(items) == 1:
            return items[0]
        return None

    def clear_selection(self) -> None:
        self._view.clearSelection()

    def iterate_items(self):
        for r in range(self._model.rowCount()):
            yield self._model.item(r, 0)

    def model(self) -> QtGui.QStandardItemModel:
        return self._model

    def view(self) -> QtWidgets.QListView:
        return self._view


class ButtonWithList(QtWidgets.QToolButton):
    def __init__(self, icon: QtGui.QIcon, text: str, parent = None) -> None:
        super().__init__(parent)
        if text:
            self.setText(text)
        if icon:
            self.setIcon(icon)
        self.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.MenuButtonPopup)

        self._menu = QtWidgets.QMenu()
        self.setMenu(self._menu)


class FilledLabel(QtWidgets.QLabel):
    def paintEvent(self, a0: QtGui.QPaintEvent | None) -> None:
        painter = QtGui.QPainter(self)

        background_color = QtWidgets.qApp.palette().text().color()

        painter.fillRect(0, 0, self.width(), self.height(), background_color)



class SpinBox(QtWidgets.QDoubleSpinBox):
    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        self.setRange(-(10**9), 10**9)
        self.setSingleStep(0.1)
        self.setValue(0)

    def wheelEvent(self, e: QtGui.QWheelEvent) -> None:
        delta = e.angleDelta().y()
        self.setValue(self.value() + (-1)**int(delta < 0) * self.singleStep())

    def setValue(self, val: float) -> None:
        self.setDecimals(3 + 3 * int(val < 1))
        super().setValue(val)



if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    w = ButtonWithList(None, "M")
    w.menu().addAction("act1")
    w.menu().addAction("act2")
    w.menu().addSeparator()
    w.menu().addAction("set...")

    w.show()

    app.exec()


