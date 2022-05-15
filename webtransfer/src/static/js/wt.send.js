function formatBytes(e) {
    if (0 === e) return "0 Bytes";
    const t = Math.floor(Math.log(e) / Math.log(1024));
    return `${parseFloat((e/Math.pow(1024,t)).toFixed(2))} ${["Bytes","KB","MB","GB"][t]}`
}

function performUpload(e) {
    let t = $("<input type = 'file'>");
    t.on("change", (t => {
        bootbox.hideAll();
        bootbox.dialog({
            message: '<div class="progress"><div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" id="progress"></div></div><p style="text-align:center;font-size:12px;margin-top:5px;" id="status"></p>',
            closeButton: !1
        });
        let n = t.target.files[0];

        function a(o) {
            $("#progress").attr("aria-valuenow", 100), $("#progress").css("width", "100%"), $("#progress").text("Upload Error"), $("#status").html(`${o}<br><a onclick = 'bootbox.hideAll();' style = 'color: var(--bs-blue); cursor: pointer;'>Click here to close this window.</a>`)
        }

        function r(t) {
            if (!t.code) t = t.responseJSON;
            if (200 !== t.code) return a(t.message); {
                let t = new FormData;
                t.append("file", n), $.ajax({
                    xhr: () => {
                        var e = new window.XMLHttpRequest;
                        return e.upload.addEventListener("progress", function(e) {
                            if (e.lengthComputable) {
                                if (e.total > 2 * Math.pow(1e3, 3)) return a("Maximum file size is 2gb, sorry for the inconvenience.");
                                let n = e.loaded / e.total,
                                    r = `${Math.round(100*n)}%`;
                                if ($("#progress").attr("aria-valuenow", 100 * n), $("#progress").css("width", r), $("#progress").text(r), 1 == n) {
                                    var t = 1;
                                    $("#status").text("Finalizing file upload..."), window.fnint = setInterval(() => {
                                        $("#status").text(`Finalizing file upload (${t}s)...`), t++
                                    }, 1e3)
                                } else $("#status").text(`${formatBytes(e.loaded)} / ${formatBytes(e.total)}`)
                            }
                        }, !1), e
                    },
                    type: "POST",
                    url: "/user/api/upload",
                    data: t,
                    contentType: !1,
                    processData: !1,
                    success: t => {
                        $.get("/user/api/fregister", {
                            name: n.name,
                            users: e.join(",")
                        }, e => {
                            if (200 !== e.code) return a("Failed while registering file data.");
                            clearInterval(window.fnint), $("#status").css("color", "var(--bs-teal)"), $("#status").html("<i class = 'bi bi-check2-circle'></i> Upload complete."), setTimeout(() => {
                                bootbox.hideAll(), window.location.reload()
                            }, 2e3)
                        })
                    }
                })
            }
        }
        $.ajax({
            type: "POST",
            url: "/user/api/preupload",
            data: {
                name: n.name,
                size: n.size
            },
            success: r,
            error: r
        })
    })), t.trigger("click");
}

function askForRecipients() {
    var e = '<style>textarea{resize:none;color:var(--fg-color-1);width:100%;border:none;height:300px;padding:10px;margin-top:5px;border-radius:5px;background-color:var(--bg-color-2);}</style><div class = "form-group"><label for = "userInput">Enter recipients:</label><br><textarea id="userInput" placeholder="Enter your recipients, each on a new line. Both usernames and IDs are supported."></textarea></div>',
        t = [],
        n = null;
    bootbox.dialog({
        title: "Select Recipients",
        message: `<div id="popup-content">${e}</div>`,
        onEscape: !0,
        buttons: {
            cancel: {
                label: "Cancel",
                className: "btn-warning"
            },
            continue: {
                label: "Continue",
                className: "btn-success",
                callback: () => {
                    if (null == n) {
                        let e = $("#userInput").val().split("\n").filter(e => e);
                        if (!e.length) return !1;
                        console.log(e);
                        $.post("/user/api/uvalidate", { users: e }, (a) => {
                            let r = "<p>Sending to the following recipients:</p><ul>";
                            for (let t of e) r += `<li style = "color: var(--bs-${a.users[t]?"teal":"red"});">${a.users[t]||t}</li>`;
                            $("#popup-content").html(r + "</ul>"), t = e, (n = !Object.values(a.users).includes(null)) || $("#popup-content").html($("#popup-content").html() + "<p>This list contains invalid users, you will have to reenter them.</p>")
                        });
                    } else n ? performUpload(t) : ($("#popup-content").html(e), $("#userInput").val(t.join("\n")), n = null);
                    return !1
                }
            }
        }
    })
}
$("#btnSendFile").on("click", askForRecipients);