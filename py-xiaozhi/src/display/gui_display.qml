import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtGraphicalEffects 1.15

Rectangle {
    id: root
    color: "#000814"
    radius: 15
    border.color: "#00d4ff"
    border.width: 2
    opacity: 0.95
    
    // Gradient background for futuristic effect
    gradient: Gradient {
        GradientStop { position: 0.0; color: "#001d3d" }
        GradientStop { position: 1.0; color: "#000814" }
    }
    
    // Glow effect
    layer.enabled: true
    layer.effect: DropShadow {
        transparentBorder: true
        color: "#00d4ff"
        radius: 20
        samples: 25
        spread: 0.2
    }

    // 信号定义 - 与 Python 回调对接
    signal manualButtonPressed()
    signal manualButtonReleased()
    signal autoButtonClicked()
    signal abortButtonClicked()
    signal modeButtonClicked()
    signal sendButtonClicked(string text)
    signal settingsButtonClicked()
    // 标题栏相关信号
    signal titleMinimize()
    signal titleClose()
    signal titleDragStart(real mouseX, real mouseY)
    signal titleDragMoveTo(real mouseX, real mouseY)
    signal titleDragEnd()

    // 主布局
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 0
        spacing: 0

        // 自定义标题栏：最小化、关闭、可拖动
        Rectangle {
            id: titleBar
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            color: "transparent"
            border.width: 0
            
            // Holographic line at bottom
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: "#00d4ff"
                opacity: 0.6
            }

            // 整条标题栏拖动（使用屏幕坐标，避免累计误差导致抖动）
            // 放在最底层，让按钮的 MouseArea 可以优先响应
            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton
                onPressed: {
                    root.titleDragStart(mouse.x, mouse.y)
                }
                onPositionChanged: {
                    if (pressed) {
                        root.titleDragMoveTo(mouse.x, mouse.y)
                    }
                }
                onReleased: {
                    root.titleDragEnd()
                }
                z: 0  // 最底层
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 8
                spacing: 8
                z: 1  // 按钮层在拖动层上方

                // 左侧拖动区域
                Item { id: dragArea; Layout.fillWidth: true; Layout.fillHeight: true }

                // 最小化
                Rectangle {
                    id: btnMin
                    width: 24; height: 24; radius: 6
                    color: btnMinMouse.pressed ? "#003566" : (btnMinMouse.containsMouse ? "#004d8f" : "transparent")
                    border.color: btnMinMouse.containsMouse ? "#00d4ff" : "#003566"
                    border.width: 1
                    z: 2  // 确保按钮在最上层
                    Text {
                        anchors.centerIn: parent;
                        text: "–";
                        font.pixelSize: 14;
                        color: btnMinMouse.containsMouse ? "#00d4ff" : "#8b9dc3"
                    }
                    MouseArea {
                        id: btnMinMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: root.titleMinimize()
                    }
                }

                // 关闭
                Rectangle {
                    id: btnClose
                    width: 24; height: 24; radius: 6
                    color: btnCloseMouse.pressed ? "#8b0000" : (btnCloseMouse.containsMouse ? "#dc143c" : "transparent")
                    border.color: btnCloseMouse.containsMouse ? "#ff4757" : "#8b0000"
                    border.width: 1
                    z: 2  // 确保按钮在最上层
                    Text {
                        anchors.centerIn: parent;
                        text: "×";
                        font.pixelSize: 14;
                        color: btnCloseMouse.containsMouse ? "#ff4757" : "#8b9dc3"
                    }
                    MouseArea {
                        id: btnCloseMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: root.titleClose()
                    }
                }
            }
        }

        // 状态卡片区域
        Rectangle {
            id: statusCard
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "transparent"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 12

                // 状态标签
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    color: "transparent"
                    border.color: "#00d4ff"
                    border.width: 1
                    radius: 10

                    Text {
                        anchors.centerIn: parent
                        text: displayModel ? displayModel.statusText : "Trạng thái: Chưa kết nối"
                        font.family: "Consolas, Monaco, monospace"
                        font.pixelSize: 14
                        font.weight: Font.Bold
                        color: "#00d4ff"
                    }
                    
                    // Holographic glow effect
                    layer.enabled: true
                    layer.effect: Glow {
                        color: "#00d4ff"
                        radius: 8
                        samples: 16
                        spread: 0.3
                    }
                }

                // 表情显示区域
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 80

                    // 动态加载表情：AnimatedImage 用于 GIF，Image 用于静态图，Text 用于 emoji
                    Loader {
                        id: emotionLoader
                        anchors.centerIn: parent
                        // 保持正方形，取宽高中较小值的 70%，最小60px
                        property real maxSize: Math.max(Math.min(parent.width, parent.height) * 0.7, 60)
                        width: maxSize
                        height: maxSize

                        sourceComponent: {
                            var path = displayModel ? displayModel.emotionPath : ""
                            if (!path || path.length === 0) {
                                return emojiComponent
                            }
                            if (path.indexOf(".gif") !== -1) {
                                return gifComponent
                            }
                            if (path.indexOf(".") !== -1) {
                                return imageComponent
                            }
                            return emojiComponent
                        }

                        // GIF 动图组件
                        Component {
                            id: gifComponent
                            AnimatedImage {
                                fillMode: Image.PreserveAspectCrop
                                source: displayModel ? displayModel.emotionPath : ""
                                playing: true
                                speed: 1.05
                                cache: true
                                clip: true
                                onStatusChanged: {
                                    if (status === Image.Error) {
                                        console.error("AnimatedImage error:", errorString, "src=", source)
                                    }
                                }
                            }
                        }

                        // 静态图片组件
                        Component {
                            id: imageComponent
                            Image {
                                fillMode: Image.PreserveAspectCrop
                                source: displayModel ? displayModel.emotionPath : ""
                                cache: true
                                clip: true
                                onStatusChanged: {
                                    if (status === Image.Error) {
                                        console.error("Image error:", errorString, "src=", source)
                                    }
                                }
                            }
                        }

                        // Emoji 文本组件
                        Component {
                            id: emojiComponent
                            Text {
                                text: displayModel ? displayModel.emotionPath : "😊"
                                font.pixelSize: 80
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }
                }

                // TTS 文本显示区域
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 60
                    color: "transparent"
                    border.color: "#003566"
                    border.width: 1
                    radius: 8

                    Text {
                        anchors.fill: parent
                        anchors.margins: 10
                        text: displayModel ? displayModel.ttsText : "SẴN SÀNG"
                        font.family: "Consolas, Monaco, monospace"
                        font.pixelSize: 13
                        color: "#00d4ff"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        wrapMode: Text.WordWrap
                    }
                    
                    // Subtle glow effect
                    layer.enabled: true
                    layer.effect: Glow {
                        color: "#00d4ff"
                        radius: 3
                        samples: 8
                        spread: 0.2
                    }
                }
            }
        }

        // 按钮区域（统一配色与尺寸）
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 72
            color: "transparent"
            border.color: "#003566"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                anchors.bottomMargin: 10
                spacing: 6

                // 手动模式按钮（按住说话） - 主色
                Button {
                    id: manualBtn
                    Layout.preferredWidth: 100
                    Layout.fillWidth: true
                    Layout.maximumWidth: 140
                    Layout.preferredHeight: 38
                    text: "NHẤN VÀ GIỮ ĐỂ NÓI"
                    visible: displayModel ? !displayModel.autoMode : true

                    background: Rectangle {
                        color: manualBtn.pressed ? "#003566" : (manualBtn.hovered ? "#0066cc" : "#00d4ff")
                        radius: 8
                        border.color: "#00d4ff"
                        border.width: 1

                        Behavior on color { ColorAnimation { duration: 120; easing.type: Easing.OutCubic } }
                    }

                    contentItem: Text {
                        text: manualBtn.text
                        font.family: "Consolas, Monaco, monospace"
                        font.pixelSize: 11
                        font.weight: Font.Bold
                        color: "black"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }

                    onPressed: { manualBtn.text = "THẢ ĐỂ DỪNG"; root.manualButtonPressed() }
                    onReleased: { manualBtn.text = "NHẤN VÀ GIỮ ĐỂ NÓI"; root.manualButtonReleased() }
                    
                    // Glow effect
                    layer.enabled: true
                    layer.effect: Glow {
                        color: "#00d4ff"
                        radius: 6
                        samples: 12
                        spread: 0.4
                    }
                }

                // 自动模式按钮 - 主色
                Button {
                    id: autoBtn
                    Layout.preferredWidth: 100
                    Layout.fillWidth: true
                    Layout.maximumWidth: 140
                    Layout.preferredHeight: 38
                    text: displayModel ? displayModel.buttonText : "BẮT ĐẦU HỘI THOẠI"
                    visible: displayModel ? displayModel.autoMode : false

                    background: Rectangle {
                        color: autoBtn.pressed ? "#003566" : (autoBtn.hovered ? "#0066cc" : "#00d4ff")
                        radius: 8
                        border.color: "#00d4ff"
                        border.width: 1
                        Behavior on color { ColorAnimation { duration: 120; easing.type: Easing.OutCubic } }
                    }

                    contentItem: Text {
                        text: autoBtn.text
                        font.family: "Consolas, Monaco, monospace"
                        font.pixelSize: 11
                        font.weight: Font.Bold
                        color: "black"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }
                    onClicked: root.autoButtonClicked()
                    
                    // Glow effect
                    layer.enabled: true
                    layer.effect: Glow {
                        color: "#00d4ff"
                        radius: 6
                        samples: 12
                        spread: 0.4
                    }
                }

                // 打断对话 - 次要色
                Button {
                    id: abortBtn
                    Layout.preferredWidth: 80
                    Layout.fillWidth: true
                    Layout.maximumWidth: 120
                    Layout.preferredHeight: 38
                    text: "NGẮT HỘI THOẠI"

                    background: Rectangle {
                        color: abortBtn.pressed ? "#8b0000" : (abortBtn.hovered ? "#dc143c" : "transparent")
                        radius: 8
                        border.color: "#ff4757"
                        border.width: 1
                    }
                    contentItem: Text {
                        text: abortBtn.text
                        font.family: "Consolas, Monaco, monospace"
                        font.pixelSize: 11
                        font.weight: Font.Bold
                        color: "#ff4757"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }
                    onClicked: root.abortButtonClicked()
                    
                    // Red glow effect
                    layer.enabled: true
                    layer.effect: Glow {
                        color: "#ff4757"
                        radius: 4
                        samples: 8
                        spread: 0.3
                    }
                }

                // 输入 + 发送
                RowLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 120
                    Layout.preferredHeight: 38
                    spacing: 6

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 38
                        color: "white"
                        radius: 8
                        border.color: textInput.activeFocus ? "#165dff" : "#e5e6eb"
                        border.width: 1

                        TextInput {
                            id: textInput
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10
                            verticalAlignment: TextInput.AlignVCenter
                            font.family: "PingFang SC, Microsoft YaHei UI"
                            font.pixelSize: 12
                            color: "#333333"
                            selectByMouse: true
                            clip: true

                            // 占位符
                            Text { anchors.fill: parent; text: "Nhập văn bản..."; font: textInput.font; color: "#c9cdd4"; verticalAlignment: Text.AlignVCenter; visible: !textInput.text && !textInput.activeFocus }

                            Keys.onReturnPressed: { if (textInput.text.trim().length > 0) { root.sendButtonClicked(textInput.text); textInput.text = "" } }
                        }
                    }

                    Button {
                        id: sendBtn
                        Layout.preferredWidth: 60
                        Layout.maximumWidth: 84
                        Layout.preferredHeight: 38
                        text: "Gửi"
                        background: Rectangle { color: sendBtn.pressed ? "#0e42d2" : (sendBtn.hovered ? "#4080ff" : "#165dff"); radius: 8 }
                        contentItem: Text {
                            text: sendBtn.text
                            font.family: "PingFang SC, Microsoft YaHei UI"
                            font.pixelSize: 12
                            color: "white"
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        onClicked: { if (textInput.text.trim().length > 0) { root.sendButtonClicked(textInput.text); textInput.text = "" } }
                    }
                }

                // 模式（次要）
                Button {
                    id: modeBtn
                    Layout.preferredWidth: 80
                    Layout.fillWidth: true
                    Layout.maximumWidth: 120
                    Layout.preferredHeight: 38
                    text: displayModel ? displayModel.modeText : "HỘI THOẠI THỦ CÔNG"
                    background: Rectangle {
                        color: modeBtn.pressed ? "#003566" : (modeBtn.hovered ? "#004d8f" : "transparent")
                        radius: 8
                        border.color: modeBtn.hovered ? "#00d4ff" : "#003566"
                        border.width: 1
                    }
                    contentItem: Text {
                        text: modeBtn.text
                        font.family: "Consolas, Monaco, monospace"
                        font.pixelSize: 10
                        font.weight: Font.Bold
                        color: modeBtn.hovered ? "#00d4ff" : "#8b9dc3"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }
                    onClicked: root.modeButtonClicked()
                    
                    // Subtle glow effect
                    layer.enabled: true
                    layer.effect: Glow {
                        color: "#00d4ff"
                        radius: 3
                        samples: 6
                        spread: 0.2
                    }
                }

                // 设置（次要）
                Button {
                    id: settingsBtn
                    Layout.preferredWidth: 80
                    Layout.fillWidth: true
                    Layout.maximumWidth: 120
                    Layout.preferredHeight: 38
                    text: "CẤU HÌNH"
                    background: Rectangle {
                        color: settingsBtn.pressed ? "#003566" : (settingsBtn.hovered ? "#004d8f" : "transparent")
                        radius: 8
                        border.color: settingsBtn.hovered ? "#00d4ff" : "#003566"
                        border.width: 1
                    }
                    contentItem: Text {
                        text: settingsBtn.text
                        font.family: "Consolas, Monaco, monospace"
                        font.pixelSize: 11
                        font.weight: Font.Bold
                        color: settingsBtn.hovered ? "#00d4ff" : "#8b9dc3"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }
                    onClicked: root.settingsButtonClicked()
                    
                    // Subtle glow effect
                    layer.enabled: true
                    layer.effect: Glow {
                        color: "#00d4ff"
                        radius: 3
                        samples: 6
                        spread: 0.2
                    }
                }
            }
        }
    }
}
