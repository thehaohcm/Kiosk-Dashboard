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
    focus: true
    
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

    // Xử lý phím Space để kích hoạt chức năng nói
    Keys.onPressed: {
        if (event.key === Qt.Key_Space && !event.isAutoRepeat) {
            // Chỉ kích hoạt khi đang ở chế độ thủ công (manual mode) và không đang nhập văn bản
            if (displayModel && !displayModel.autoMode && !textInput.activeFocus) {
                // Đảm bảo root có focus để nhận phím
                root.forceActiveFocus()
                
                manualBtn.text = "THẢ ĐỂ DỪNG"
                root.manualButtonPressed()
                event.accepted = true
            }
        }
        // Phím C để ngắt hội thoại
        else if (event.key === Qt.Key_C && !textInput.activeFocus) {
            root.abortButtonClicked()
            root.forceActiveFocus()
            event.accepted = true
        }
        // Phím I để focus vào textbox
        else if (event.key === Qt.Key_I && !textInput.activeFocus) {
            textInput.forceActiveFocus()
            event.accepted = true
        }
        // Phím Esc để focus ra ngoài root
        else if (event.key === Qt.Key_Escape) {
            root.forceActiveFocus()
            event.accepted = true
        }
    }
    
    Keys.onReleased: {
        if (event.key === Qt.Key_Space && !event.isAutoRepeat) {
            // Chỉ kích hoạt khi đang ở chế độ thủ công (manual mode) và không đang nhập văn bản
            if (displayModel && !displayModel.autoMode && !textInput.activeFocus) {
                // Đảm bảo root có focus để nhận phím
                root.forceActiveFocus()
                
                manualBtn.text = "NHẤN VÀ GIỮ ĐỂ NÓI"
                root.manualButtonReleased()
                event.accepted = true
            }
        }
    }

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
                        // Tăng kích thước lên 95% để bao quát gần như toàn bộ khung
                        property real maxSize: Math.max(Math.min(parent.width, parent.height) * 0.95, 120)
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
                            Item {
                                // Danh sách emotion keywords được vẽ bằng code
                                property var codeEmotions: ["happy", "sad", "thinking", "surprised", "neutral", "angry", "confused", "love", "wink", "winking",
                                                           "crying", "embarrassed", "funny", "laughing", "relaxed", "shocked", "silly", "sleepy",
                                                           "cool", "confident", "delicious", "kissy", "loving"]
                                property bool isCodeEmotion: displayModel && displayModel.emotionPath && codeEmotions.indexOf(displayModel.emotionPath) !== -1
                                property bool isEmojiText: displayModel && displayModel.emotionPath && displayModel.emotionPath.length > 0 && displayModel.emotionPath.length <= 4 && !isCodeEmotion
                                
                                // Nếu là emoji text thì hiển thị text
                                Text {
                                    visible: isEmojiText
                                    anchors.centerIn: parent
                                    text: displayModel ? displayModel.emotionPath : "😊"
                                    font.pixelSize: 80
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                
                                // Nếu là keyword hoặc empty thì vẽ bằng Canvas
                                Canvas {
                                    visible: !isEmojiText
                                    anchors.fill: parent
                                    
                                    property string emotion: displayModel ? displayModel.emotionPath : "happy"
                                    
                                    onEmotionChanged: {
                                        console.log("Emotion changed to:", emotion)
                                        requestPaint()
                                    }
                                    
                                    onPaint: {
                                        var ctx = getContext("2d")
                                        var w = width
                                        var h = height
                                        var centerX = w / 2
                                        var centerY = h / 2
                                        
                                        ctx.clearRect(0, 0, w, h)
                                        
                                        // Thiết lập màu và style
                                        ctx.strokeStyle = "#00d4ff"
                                        ctx.fillStyle = "#00d4ff"
                                        ctx.lineWidth = 4
                                        ctx.lineCap = "round"
                                        ctx.lineJoin = "round"
                                        
                                        // Kích thước các thành phần
                                        var eyeWidth = w * 0.18
                                        var eyeHeight = h * 0.12
                                        var eyeY = centerY - h * 0.12
                                        var eyeSpacing = w * 0.15
                                        
                                        var mouthY = centerY + h * 0.15
                                        var mouthWidth = w * 0.4
                                        var mouthHeight = h * 0.08
                                        
                                        // Vẽ theo emotion
                                        if (emotion === "neutral") {
                                            // 😐 NEUTRAL - Mắt bình thường, miệng thẳng
                                            // Mắt trái
                                            ctx.fillRect(centerX - eyeSpacing - eyeWidth, eyeY, eyeWidth, eyeHeight)
                                            // Mắt phải
                                            ctx.fillRect(centerX + eyeSpacing, eyeY, eyeWidth, eyeHeight)
                                            
                                            // Miệng thẳng (không cảm xúc)
                                            ctx.beginPath()
                                            ctx.moveTo(centerX - mouthWidth*0.3, mouthY)
                                            ctx.lineTo(centerX + mouthWidth*0.3, mouthY)
                                            ctx.stroke()
                                            
                                        } else if (emotion === "happy" || emotion === "" || !emotion) {
                                            // 😊 HAPPY - Mắt chữ nhật bo góc, miệng cong cười
                                            // Mắt trái
                                            ctx.fillStyle = "#00d4ff"
                                            ctx.fillRect(centerX - eyeSpacing - eyeWidth, eyeY, eyeWidth, eyeHeight)
                                            // Mắt phải
                                            ctx.fillRect(centerX + eyeSpacing, eyeY, eyeWidth, eyeHeight)
                                            
                                            // Miệng cười (đường cong)
                                            ctx.beginPath()
                                            ctx.arc(centerX, mouthY - mouthHeight, mouthWidth/2, 0.3 * Math.PI, 0.7 * Math.PI)
                                            ctx.stroke()
                                            
                                        } else if (emotion === "sad") {
                                            // 😢 SAD - Mắt chữ nhật nghiêng, miệng cong xuống
                                            ctx.save()
                                            // Mắt trái nghiêng
                                            ctx.translate(centerX - eyeSpacing - eyeWidth/2, eyeY + eyeHeight/2)
                                            ctx.rotate(-0.2)
                                            ctx.fillRect(-eyeWidth/2, -eyeHeight/2, eyeWidth, eyeHeight)
                                            ctx.restore()
                                            
                                            ctx.save()
                                            // Mắt phải nghiêng
                                            ctx.translate(centerX + eyeSpacing + eyeWidth/2, eyeY + eyeHeight/2)
                                            ctx.rotate(0.2)
                                            ctx.fillRect(-eyeWidth/2, -eyeHeight/2, eyeWidth, eyeHeight)
                                            ctx.restore()
                                            
                                            // Miệng buồn
                                            ctx.beginPath()
                                            ctx.arc(centerX, mouthY + mouthHeight * 2, mouthWidth/2, 1.3 * Math.PI, 1.7 * Math.PI)
                                            ctx.stroke()
                                            
                                        } else if (emotion === "thinking") {
                                            // 🤔 THINKING - Mắt nhỏ, miệng nhỏ ngang
                                            // Mắt trái (nhỏ hơn)
                                            ctx.fillRect(centerX - eyeSpacing - eyeWidth*0.8, eyeY + eyeHeight*0.2, eyeWidth*0.8, eyeHeight*0.8)
                                            // Mắt phải (nhỏ hơn)
                                            ctx.fillRect(centerX + eyeSpacing, eyeY + eyeHeight*0.2, eyeWidth*0.8, eyeHeight*0.8)
                                            
                                            // Miệng ngang ngắn
                                            ctx.beginPath()
                                            ctx.moveTo(centerX - mouthWidth*0.3, mouthY)
                                            ctx.lineTo(centerX + mouthWidth*0.3, mouthY)
                                            ctx.stroke()
                                            
                                            // Dấu "..."
                                            ctx.font = w * 0.15 + "px monospace"
                                            ctx.fillText("...", centerX + w*0.25, centerY - h*0.15)
                                            
                                        } else if (emotion === "surprised") {
                                            // 😮 SURPRISED - Mắt to, miệng hình chữ O
                                            // Mắt trái (to hơn, chỉ viền)
                                            ctx.strokeRect(centerX - eyeSpacing - eyeWidth*1.2, eyeY - eyeHeight*0.2, eyeWidth*1.2, eyeHeight*1.4)
                                            // Mắt phải (to hơn, chỉ viền)
                                            ctx.strokeRect(centerX + eyeSpacing, eyeY - eyeHeight*0.2, eyeWidth*1.2, eyeHeight*1.4)
                                            
                                            // Miệng hình O
                                            ctx.beginPath()
                                            ctx.arc(centerX, mouthY, mouthWidth*0.25, 0, 2 * Math.PI)
                                            ctx.stroke()
                                            
                                        } else if (emotion === "angry") {
                                            // 😠 ANGRY - Mắt nghiêng xuống trong, miệng zigzag
                                            ctx.lineWidth = 5
                                            
                                            // "Lông mày" giận - đường nghiêng
                                            ctx.beginPath()
                                            ctx.moveTo(centerX - eyeSpacing - eyeWidth*1.2, eyeY - eyeHeight*0.8)
                                            ctx.lineTo(centerX - eyeSpacing + eyeWidth*0.2, eyeY - eyeHeight*0.2)
                                            ctx.stroke()
                                            
                                            ctx.beginPath()
                                            ctx.moveTo(centerX + eyeSpacing + eyeWidth*1.2, eyeY - eyeHeight*0.8)
                                            ctx.lineTo(centerX + eyeSpacing - eyeWidth*0.2, eyeY - eyeHeight*0.2)
                                            ctx.stroke()
                                            
                                            ctx.lineWidth = 4
                                            // Mắt trái
                                            ctx.fillRect(centerX - eyeSpacing - eyeWidth, eyeY, eyeWidth, eyeHeight)
                                            // Mắt phải
                                            ctx.fillRect(centerX + eyeSpacing, eyeY, eyeWidth, eyeHeight)
                                            
                                            // Miệng zigzag
                                            ctx.beginPath()
                                            ctx.moveTo(centerX - mouthWidth*0.4, mouthY)
                                            ctx.lineTo(centerX - mouthWidth*0.2, mouthY + mouthHeight*0.8)
                                            ctx.lineTo(centerX, mouthY)
                                            ctx.lineTo(centerX + mouthWidth*0.2, mouthY + mouthHeight*0.8)
                                            ctx.lineTo(centerX + mouthWidth*0.4, mouthY)
                                            ctx.stroke()
                                            
                                        } else if (emotion === "confused") {
                                            // 😕 CONFUSED - Mắt lệch độ cao, miệng nghiêng
                                            // Mắt trái
                                            ctx.fillRect(centerX - eyeSpacing - eyeWidth, eyeY, eyeWidth, eyeHeight)
                                            // Mắt phải (cao hơn)
                                            ctx.fillRect(centerX + eyeSpacing, eyeY - eyeHeight*0.5, eyeWidth, eyeHeight)
                                            
                                            // Miệng nghiêng
                                            ctx.beginPath()
                                            ctx.moveTo(centerX - mouthWidth*0.3, mouthY)
                                            ctx.lineTo(centerX + mouthWidth*0.3, mouthY + mouthHeight*0.8)
                                            ctx.stroke()
                                            
                                            // Dấu "?"
                                            ctx.font = w * 0.12 + "px monospace"
                                            ctx.fillText("?", centerX + w*0.28, centerY - h*0.18)
                                            
                                        } else if (emotion === "love") {
                                            // 😍 LOVE - Mắt hình trái tim
                                            // Vẽ trái tim trái
                                            var heartX = centerX - eyeSpacing - eyeWidth/2
                                            var heartY = eyeY + eyeHeight/2
                                            var heartSize = eyeWidth * 0.7
                                            
                                            ctx.beginPath()
                                            ctx.moveTo(heartX, heartY + heartSize*0.3)
                                            ctx.bezierCurveTo(heartX, heartY, heartX - heartSize*0.5, heartY - heartSize*0.3, heartX, heartY - heartSize*0.3)
                                            ctx.bezierCurveTo(heartX + heartSize*0.5, heartY - heartSize*0.3, heartX, heartY, heartX, heartY + heartSize*0.3)
                                            ctx.fill()
                                            
                                            // Vẽ trái tim phải
                                            heartX = centerX + eyeSpacing + eyeWidth/2
                                            ctx.beginPath()
                                            ctx.moveTo(heartX, heartY + heartSize*0.3)
                                            ctx.bezierCurveTo(heartX, heartY, heartX - heartSize*0.5, heartY - heartSize*0.3, heartX, heartY - heartSize*0.3)
                                            ctx.bezierCurveTo(heartX + heartSize*0.5, heartY - heartSize*0.3, heartX, heartY, heartX, heartY + heartSize*0.3)
                                            ctx.fill()
                                            
                                            // Miệng cười
                                            ctx.beginPath()
                                            ctx.arc(centerX, mouthY - mouthHeight, mouthWidth/2, 0.3 * Math.PI, 0.7 * Math.PI)
                                            ctx.stroke()
                                            
                                        } else if (emotion === "wink" || emotion === "winking") {
                                            // 😉 WINK - Một mắt nhắm (đường ngang), một mắt mở
                                            // Mắt trái nhắm
                                            ctx.beginPath()
                                            ctx.moveTo(centerX - eyeSpacing - eyeWidth, eyeY + eyeHeight/2)
                                            ctx.lineTo(centerX - eyeSpacing, eyeY + eyeHeight/2)
                                            ctx.stroke()
                                            
                                            // Mắt phải mở
                                            ctx.fillRect(centerX + eyeSpacing, eyeY, eyeWidth, eyeHeight)
                                            
                                            // Miệng cười
                                            ctx.beginPath()
                                            ctx.arc(centerX, mouthY - mouthHeight, mouthWidth/2, 0.3 * Math.PI, 0.7 * Math.PI)
                                            ctx.stroke()
                                            
                                        } else if (emotion === "crying") {
                                            // 😭 CRYING - Mắt nhắm, nước mắt chảy, miệng khóc
                                            // Mắt nhắm (đường cong)
                                            ctx.beginPath()
                                            ctx.arc(centerX - eyeSpacing - eyeWidth/2, eyeY + eyeHeight/2, eyeWidth*0.6, 0, Math.PI)
                                            ctx.stroke()
                                            ctx.beginPath()
                                            ctx.arc(centerX + eyeSpacing + eyeWidth/2, eyeY + eyeHeight/2, eyeWidth*0.6, 0, Math.PI)
                                            ctx.stroke()
                                            
                                            // Nước mắt (giọt lớn)
                                            ctx.beginPath()
                                            ctx.arc(centerX - eyeSpacing - eyeWidth/2, eyeY + eyeHeight*2, eyeWidth*0.3, 0, 2 * Math.PI)
                                            ctx.fill()
                                            ctx.beginPath()
                                            ctx.arc(centerX + eyeSpacing + eyeWidth/2, eyeY + eyeHeight*2.5, eyeWidth*0.25, 0, 2 * Math.PI)
                                            ctx.fill()
                                            
                                            // Miệng khóc (cong xuống mạnh)
                                            ctx.beginPath()
                                            ctx.arc(centerX, mouthY + mouthHeight * 2.5, mouthWidth/2, 1.2 * Math.PI, 1.8 * Math.PI)
                                            ctx.stroke()
                                            
                                        } else if (emotion === "embarrassed") {
                                            // 😳 EMBARRASSED - Mắt nhìn sang, má đỏ, miệng nhỏ
                                            // Mắt nhìn sang (chữ nhật nhỏ bên cạnh)
                                            ctx.fillRect(centerX - eyeSpacing - eyeWidth*0.5, eyeY, eyeWidth*0.6, eyeHeight*0.8)
                                            ctx.fillRect(centerX + eyeSpacing + eyeWidth*0.4, eyeY, eyeWidth*0.6, eyeHeight*0.8)
                                            
                                            // "Má đỏ" (dấu gạch)
                                            ctx.lineWidth = 2
                                            for(var i = 0; i < 3; i++) {
                                                ctx.beginPath()
                                                ctx.moveTo(centerX - mouthWidth*0.6, mouthY - mouthHeight*0.5 + i*eyeHeight*0.3)
                                                ctx.lineTo(centerX - mouthWidth*0.4, mouthY - mouthHeight*0.5 + i*eyeHeight*0.3)
                                                ctx.stroke()
                                                ctx.beginPath()
                                                ctx.moveTo(centerX + mouthWidth*0.4, mouthY - mouthHeight*0.5 + i*eyeHeight*0.3)
                                                ctx.lineTo(centerX + mouthWidth*0.6, mouthY - mouthHeight*0.5 + i*eyeHeight*0.3)
                                                ctx.stroke()
                                            }
                                            ctx.lineWidth = 4
                                            
                                            // Miệng nhỏ
                                            ctx.beginPath()
                                            ctx.arc(centerX, mouthY, mouthWidth*0.15, 0, Math.PI)
                                            ctx.stroke()
                                            
                                        } else if (emotion === "funny" || emotion === "laughing") {
                                            // 🤣 FUNNY/LAUGHING - Mắt nhắm cười, miệng há to
                                            // Mắt nhắm cười (dấu ^)
                                            ctx.beginPath()
                                            ctx.moveTo(centerX - eyeSpacing - eyeWidth, eyeY + eyeHeight/2)
                                            ctx.lineTo(centerX - eyeSpacing - eyeWidth/2, eyeY - eyeHeight*0.2)
                                            ctx.lineTo(centerX - eyeSpacing, eyeY + eyeHeight/2)
                                            ctx.stroke()
                                            
                                            ctx.beginPath()
                                            ctx.moveTo(centerX + eyeSpacing, eyeY + eyeHeight/2)
                                            ctx.lineTo(centerX + eyeSpacing + eyeWidth/2, eyeY - eyeHeight*0.2)
                                            ctx.lineTo(centerX + eyeSpacing + eyeWidth, eyeY + eyeHeight/2)
                                            ctx.stroke()
                                            
                                            // Miệng cười lớn (chữ D)
                                            ctx.lineWidth = 5
                                            ctx.beginPath()
                                            ctx.arc(centerX, mouthY - mouthHeight*0.5, mouthWidth*0.6, 0.2 * Math.PI, 0.8 * Math.PI)
                                            ctx.stroke()
                                            ctx.lineWidth = 4
                                            
                                        } else if (emotion === "relaxed") {
                                            // 😌 RELAXED - Mắt nhắm nhẹ, miệng cười nhẹ
                                            // Mắt nhắm (đường ngang nhẹ cong)
                                            ctx.beginPath()
                                            ctx.moveTo(centerX - eyeSpacing - eyeWidth, eyeY + eyeHeight/2)
                                            ctx.quadraticCurveTo(centerX - eyeSpacing - eyeWidth/2, eyeY + eyeHeight*0.8, centerX - eyeSpacing, eyeY + eyeHeight/2)
                                            ctx.stroke()
                                            ctx.beginPath()
                                            ctx.moveTo(centerX + eyeSpacing, eyeY + eyeHeight/2)
                                            ctx.quadraticCurveTo(centerX + eyeSpacing + eyeWidth/2, eyeY + eyeHeight*0.8, centerX + eyeSpacing + eyeWidth, eyeY + eyeHeight/2)
                                            ctx.stroke()
                                            
                                            // Miệng cười nhẹ
                                            ctx.beginPath()
                                            ctx.arc(centerX, mouthY - mouthHeight*0.5, mouthWidth*0.4, 0.3 * Math.PI, 0.7 * Math.PI)
                                            ctx.stroke()
                                            
                                        } else if (emotion === "shocked") {
                                            // 😱 SHOCKED - Mắt to tròn, miệng há hốc
                                            // Mắt to (hình tròn to)
                                            ctx.beginPath()
                                            ctx.arc(centerX - eyeSpacing - eyeWidth/2, eyeY + eyeHeight/2, eyeWidth*0.8, 0, 2 * Math.PI)
                                            ctx.stroke()
                                            ctx.beginPath()
                                            ctx.arc(centerX + eyeSpacing + eyeWidth/2, eyeY + eyeHeight/2, eyeWidth*0.8, 0, 2 * Math.PI)
                                            ctx.stroke()
                                            
                                            // Miệng há hốc (hình oval dọc)
                                            ctx.beginPath()
                                            ctx.ellipse(centerX, mouthY + mouthHeight, mouthWidth*0.25, mouthHeight*1.5, 0, 0, 2 * Math.PI)
                                            ctx.stroke()
                                            
                                        } else if (emotion === "silly") {
                                            // 🤪 SILLY - Mắt lệch, lưỡi lè
                                            // Mắt lệch
                                            ctx.fillRect(centerX - eyeSpacing - eyeWidth*0.7, eyeY - eyeHeight*0.3, eyeWidth*0.8, eyeHeight*0.8)
                                            ctx.strokeRect(centerX + eyeSpacing, eyeY + eyeHeight*0.2, eyeWidth*1.2, eyeHeight*1.2)
                                            
                                            // Miệng nghiêng với lưỡi
                                            ctx.beginPath()
                                            ctx.moveTo(centerX - mouthWidth*0.2, mouthY)
                                            ctx.lineTo(centerX + mouthWidth*0.3, mouthY + mouthHeight)
                                            ctx.stroke()
                                            
                                            // Lưỡi lè
                                            ctx.fillStyle = "#00d4ff"
                                            ctx.beginPath()
                                            ctx.ellipse(centerX + mouthWidth*0.35, mouthY + mouthHeight*1.5, mouthWidth*0.15, mouthHeight*0.8, Math.PI/4, 0, 2 * Math.PI)
                                            ctx.fill()
                                            
                                        } else if (emotion === "sleepy") {
                                            // 😴 SLEEPY - Mắt nhắm cong xuống như ngủ, "Zzz" phía trên
                                            // Mắt nhắm cong (như đang ngủ)
                                            ctx.beginPath()
                                            ctx.arc(centerX - eyeSpacing - eyeWidth/2, eyeY + eyeHeight/2, eyeWidth*0.6, 0, Math.PI)
                                            ctx.stroke()
                                            ctx.beginPath()
                                            ctx.arc(centerX + eyeSpacing + eyeWidth/2, eyeY + eyeHeight/2, eyeWidth*0.6, 0, Math.PI)
                                            ctx.stroke()
                                            
                                            // Miệng nhỏ mở (hơi há)
                                            ctx.beginPath()
                                            ctx.arc(centerX, mouthY, mouthWidth*0.15, 0, Math.PI)
                                            ctx.stroke()
                                            
                                            // Zzz bay lên phía trên
                                            ctx.fillStyle = "#00d4ff"
                                            ctx.font = "bold " + (w * 0.14) + "px monospace"
                                            ctx.fillText("Z", centerX + w*0.22, eyeY - h*0.05)
                                            ctx.font = "bold " + (w * 0.11) + "px monospace"
                                            ctx.fillText("z", centerX + w*0.30, eyeY - h*0.12)
                                            ctx.font = "bold " + (w * 0.08) + "px monospace"
                                            ctx.fillText("z", centerX + w*0.36, eyeY - h*0.17)
                                            
                                        } else if (emotion === "cool" || emotion === "confident") {
                                            // 😎 COOL/CONFIDENT - Kính đen, miệng mỉm cười
                                            // Kính đen (chữ nhật đen to)
                                            ctx.fillStyle = "#00d4ff"
                                            ctx.fillRect(centerX - eyeSpacing - eyeWidth*1.3, eyeY - eyeHeight*0.2, eyeWidth*1.3, eyeHeight*1.3)
                                            ctx.fillRect(centerX + eyeSpacing, eyeY - eyeHeight*0.2, eyeWidth*1.3, eyeHeight*1.3)
                                            
                                            // Cầu nối kính
                                            ctx.fillRect(centerX - eyeWidth*0.15, eyeY + eyeHeight*0.2, eyeWidth*0.3, eyeHeight*0.3)
                                            
                                            // Miệng mỉm cười tự tin
                                            ctx.beginPath()
                                            ctx.moveTo(centerX - mouthWidth*0.3, mouthY)
                                            ctx.quadraticCurveTo(centerX, mouthY + mouthHeight*0.5, centerX + mouthWidth*0.3, mouthY)
                                            ctx.stroke()
                                            
                                        } else if (emotion === "delicious" || emotion === "kissy") {
                                            // 😋 DELICIOUS/KISSY - Mắt vui, lưỡi liếm môi / môi chu
                                            // Mắt
                                            ctx.fillRect(centerX - eyeSpacing - eyeWidth, eyeY, eyeWidth, eyeHeight)
                                            ctx.fillRect(centerX + eyeSpacing, eyeY, eyeWidth, eyeHeight)
                                            
                                            if (emotion === "delicious") {
                                                // Lưỡi liếm môi
                                                ctx.beginPath()
                                                ctx.arc(centerX, mouthY - mouthHeight, mouthWidth*0.4, 0.2 * Math.PI, 0.8 * Math.PI)
                                                ctx.stroke()
                                                
                                                // Lưỡi
                                                ctx.fillStyle = "#00d4ff"
                                                ctx.beginPath()
                                                ctx.ellipse(centerX - mouthWidth*0.35, mouthY - mouthHeight*1.2, mouthWidth*0.12, mouthHeight*0.6, -Math.PI/4, 0, 2 * Math.PI)
                                                ctx.fill()
                                            } else {
                                                // Môi chu (hình chữ O nhỏ)
                                                ctx.beginPath()
                                                ctx.arc(centerX, mouthY, mouthWidth*0.2, 0, 2 * Math.PI)
                                                ctx.stroke()
                                                
                                                // Tim nhỏ bay lên
                                                var tinyHeartX = centerX + w*0.25
                                                var tinyHeartY = centerY - h*0.15
                                                var tinySize = w*0.04
                                                ctx.fillStyle = "#00d4ff"
                                                ctx.font = tinySize + "px Arial"
                                                ctx.fillText("♥", tinyHeartX, tinyHeartY)
                                            }
                                            
                                        } else if (emotion === "loving") {
                                            // Giống love nhưng thêm hiệu ứng
                                            var heartX = centerX - eyeSpacing - eyeWidth/2
                                            var heartY = eyeY + eyeHeight/2
                                            var heartSize = eyeWidth * 0.7
                                            
                                            ctx.beginPath()
                                            ctx.moveTo(heartX, heartY + heartSize*0.3)
                                            ctx.bezierCurveTo(heartX, heartY, heartX - heartSize*0.5, heartY - heartSize*0.3, heartX, heartY - heartSize*0.3)
                                            ctx.bezierCurveTo(heartX + heartSize*0.5, heartY - heartSize*0.3, heartX, heartY, heartX, heartY + heartSize*0.3)
                                            ctx.fill()
                                            
                                            heartX = centerX + eyeSpacing + eyeWidth/2
                                            ctx.beginPath()
                                            ctx.moveTo(heartX, heartY + heartSize*0.3)
                                            ctx.bezierCurveTo(heartX, heartY, heartX - heartSize*0.5, heartY - heartSize*0.3, heartX, heartY - heartSize*0.3)
                                            ctx.bezierCurveTo(heartX + heartSize*0.5, heartY - heartSize*0.3, heartX, heartY, heartX, heartY + heartSize*0.3)
                                            ctx.fill()
                                            
                                            ctx.beginPath()
                                            ctx.arc(centerX, mouthY - mouthHeight, mouthWidth/2, 0.3 * Math.PI, 0.7 * Math.PI)
                                            ctx.stroke()
                                            
                                        } else {
                                            // Mặc định - happy
                                            ctx.fillRect(centerX - eyeSpacing - eyeWidth, eyeY, eyeWidth, eyeHeight)
                                            ctx.fillRect(centerX + eyeSpacing, eyeY, eyeWidth, eyeHeight)
                                            ctx.beginPath()
                                            ctx.arc(centerX, mouthY - mouthHeight, mouthWidth/2, 0.3 * Math.PI, 0.7 * Math.PI)
                                            ctx.stroke()
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // TTS 文本显示区域 - với Flickable để scroll
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 80
                    Layout.preferredHeight: 120
                    color: "transparent"
                    border.color: "#003566"
                    border.width: 1
                    radius: 8

                    Flickable {
                        id: textFlickable
                        anchors.fill: parent
                        anchors.margins: 8
                        clip: true
                        contentHeight: ttsTextContent.implicitHeight
                        boundsBehavior: Flickable.StopAtBounds
                        
                        ScrollBar.vertical: ScrollBar {
                            policy: ScrollBar.AsNeeded
                            width: 8
                            contentItem: Rectangle {
                                implicitWidth: 6
                                radius: 3
                                color: parent.pressed ? "#00d4ff" : (parent.hovered ? "#0088cc" : "#003566")
                                opacity: parent.active ? 0.8 : 0.5
                            }
                        }

                        Text {
                            id: ttsTextContent
                            width: textFlickable.width - 10
                            text: displayModel ? (displayModel.conversationHistory || displayModel.ttsText || "SẴN SÀNG") : "SẴN SÀNG"
                            font.family: "Consolas, Monaco, monospace"
                            font.pixelSize: 13
                            color: "#00d4ff"
                            wrapMode: Text.WordWrap
                            textFormat: Text.PlainText
                            leftPadding: 5
                            rightPadding: 5
                            topPadding: 5
                            bottomPadding: 5
                            // Căn giữa khi text ngắn, căn trái khi text dài
                            horizontalAlignment: (displayModel && displayModel.conversationHistory && displayModel.conversationHistory.length > 50) ? Text.AlignLeft : Text.AlignHCenter
                            // Đảm bảo chiều cao tối thiểu bằng parent khi text ngắn để căn giữa
                            height: Math.max(implicitHeight, textFlickable.height)
                            verticalAlignment: Text.AlignVCenter
                            
                            // Tự động scroll xuống cuối khi có text mới
                            onTextChanged: {
                                if (displayModel && displayModel.conversationHistory) {
                                    textFlickable.contentY = Math.max(0, textFlickable.contentHeight - textFlickable.height)
                                }
                            }
                        }
                        
                        // Scroll bằng chuột
                        MouseArea {
                            anchors.fill: parent
                            onWheel: {
                                if (wheel.angleDelta.y > 0) {
                                    textFlickable.contentY = Math.max(0, textFlickable.contentY - 30)
                                } else {
                                    textFlickable.contentY = Math.min(
                                        textFlickable.contentHeight - textFlickable.height,
                                        textFlickable.contentY + 30
                                    )
                                }
                            }
                            onPressed: mouse.accepted = false
                        }
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
                    onClicked: { root.autoButtonClicked(); root.forceActiveFocus() }
                    
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
                    onClicked: { root.abortButtonClicked(); root.forceActiveFocus() }
                    
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
                        onClicked: { if (textInput.text.trim().length > 0) { root.sendButtonClicked(textInput.text); textInput.text = ""; root.forceActiveFocus() } }
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
                    onClicked: { root.modeButtonClicked(); root.forceActiveFocus() }
                    
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
                    onClicked: { root.settingsButtonClicked(); root.forceActiveFocus() }
                    
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
