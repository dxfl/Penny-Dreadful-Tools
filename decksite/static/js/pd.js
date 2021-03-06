/*global PD:true Deckbox:false FooTable:false */
window.PD = {};
PD.init = function () {
    PD.initDismiss();
    PD.initMenu();
    PD.initTables();
    PD.initDetails();
    PD.initTooltips();
    $("input[type=file]").on("change", PD.loadDeck).on("change", PD.toggleDrawDropdown);
    $(".bugtable").trigger("sorton", [[[2,0],[0,0]]]);
    $(".toggle-illegal").on("change", PD.toggleIllegalCards);
    PD.showLocalTimes();
    $.get("/api/intro/", PD.showIntro);
    $.get("/api/admin/", PD.showAdmin);
    PD.initSignupDeckChooser();
};
PD.initDismiss = function () {
    $(".dismiss").click(function () {
        alert("If you need to see this again, visit FAQs on the About menu");
        $(this).closest(".intro-container").hide();
        $.post("/api/intro/"); // Fire and forget request to set cookie to remember dismissal of intro box and not show it again.
        return false;
    });
};
PD.initMenu = function () {
    $(".has-submenu").hoverIntent({
        over: PD.onDropdownHover,
        out: PD.onDropdownLeave,
        interval: 50,
        timeout: 250
    });
};
PD.onDropdownHover = function () {
    $(this).addClass("hovering");
    $(this).find(".submenu-container").slideDown("fast");
};
PD.onDropdownLeave = function () {
    $(this).removeClass("hovering");
    $(this).find(".submenu-container").slideUp("fast");
};
PD.initTables = function () {
    var selector = "main table";

    // Apply footable to all reasonably-sized tables for a nice mobile layout.
    $(selector).filter(function () { return $(this).find("> tbody > tr").length <= 1000; }).footable({
        "toggleColumn": "last",
        "breakpoints": {
            "xs": 359,
            "sm": 639,
            "md": 799,
            "lg": 1119
        }
    }).bind("sortStart", function () {
        // Prevent expanded information from sorting first and not staying with parent row by collapsing all expanded rows before sorting.
        FooTable.get(this).rows.collapse();
    }).css({ "display": "table" });
    $(".loading").addClass("loaded");
    $(selector).css({ "visibility": "visible" });

    $.tablesorter.addParser({
        "id": "record",
        "is": function(s) {
            return s.match(/^\d+–\d+(–\d+)?$/);
        },
        "format": function(s) {
            var parts, wins, losses;
            if (s == "") {
                return "";
            }
            parts = s.split("–");
            wins = parseInt(parts[0]);
            losses = parseInt(parts[1]);
            return ((wins - losses) * 1000 + wins).toString();
        },
        "type": "numeric"
    });
    $.tablesorter.addParser({
        "id": "colors",
        "is": function(_s, _table, _td, $td) {
            return $td.find("span.mana").length > 0;
        },
        "format": function(_s, _table, td) {
            var i,
                score = 0,
                symbols = ["_", "W", "U", "B", "R", "G"];
            for (i = 0; i < symbols.length; i++) {
                if ($(td).find("span.mana-" + symbols[i]).length > 0) {
                    score += Math.pow(i, 10);
                }
            }
            return score;
        },
        "type": "numeric"
    });
    $.tablesorter.addParser({
        "id": "bugseverity",
        "is": function(s) {
            return ["Game Breaking", "Advantageous", "Disadvantageous", "Graphical", "Non-Functional ability", "Unclassified"].indexOf(s) > -1;
        },
        "format": function(s) {
            return ["Game Breaking", "Advantageous", "Disadvantageous", "Graphical", "Non-Functional ability", "Unclassified"].indexOf(s)
        },
        "type": "numeric"
    });
    $.tablesorter.addParser({
        "id": "archetype",
        is: function (_s, _table, _td, $td) {
            return $td.hasClass("initial");
        },
        "format": function(s, table, td, $td) {
            return $(td).data("sort");
        },
        "type": "numeric"
    })
    /* Give archetype columns the classes primary and secondary so that we can nest when sorted by first column but not otherwise. */
    $("table.archetypes").tablesorter({
        "sortList": [[0, 0]],
        "widgets": ["columns"],
        "widgetOptions": {"columns" : ["primary", "secondary"]}
    });
    $(selector).tablesorter({});
};
PD.initDetails = function () {
    $(".details").siblings("p.question").click(function () {
        $(this).siblings(".details").toggle();
        return false;
    });
};
// Disable tooltips on touch devices where they are awkward but enable on others where they are useful.
PD.initTooltips = function () {
    $("body").on("touchstart", function() {
        $("body").off();
    });
    $("body").on("mouseover", function() {
        if (typeof Deckbox != "undefined") {
            Deckbox._.enable();
        }
        Tipped.create("main [title]", {"showDelay": 500, "size": "large", maxWidth: "200"});
        $("body").off();
    });
}
PD.loadDeck = function () {
    var file = this.files[0],
        reader = new FileReader();
    reader.onload = function (e) {
        $("textarea").val(e.target.result);
    };
    reader.readAsText(file);
}
PD.toggleDrawDropdown = function () {
    var can_draw = false;
    $(document).find(".deckselect").each(function(_, select) {
        can_draw = can_draw || select.selectedOptions[0].classList.contains("deck-can-draw");
    });
    if (can_draw) {
        $(".draw-report").css("visibility", "visible");
    }
    else {
        $(".draw-report").css("visibility", "hidden");
        $("#draws").val(0);
    }
    return can_draw;
}
PD.toggleIllegalCards = function () {
    // Fix the width of the table columns so that it does not "jump" when rows are added or removed.
    $(".bugtable tr td").each(function() {
        $(this).css({"width": $(this).width() + "px"});
    });
    $(".bugtable").not(".footable-details").each(function () { FooTable.get(this).rows.collapse(); });
    $("tr").find(".illegal").closest("tr").toggle(!this.checked);
}
PD.showIntro = function (show) {
    if (show && !PD.getUrlParam("hide_intro")) {
        $(".intro-container").show();
    }
}
PD.showAdmin = function (show) {
    if (show) {
        $(".admin").show();
    }
}
PD.showLocalTimes = function () {
    $(".time").each(function () {
        var t = moment($(this).data("time"));
        $(this).html(t.tz(moment.tz.guess()).format("dddd h:mma z")).parent(".local").show();
    });
}
PD.getUrlParams = function () {
    var vars = [], hash, i,
        hashes = window.location.href.slice(window.location.href.indexOf("?") + 1).split("&");
    for (i = 0; i < hashes.length; i++) {
        hash = hashes[i].split("=");
        vars.push(hash[0]);
        vars[hash[0]] = hash[1];
    }
    return vars;
},
PD.getUrlParam = function (name) {
    return PD.getUrlParams()[name];
}

PD.initSignupDeckChooser = function () {
    $("#signup_recent_decks").on("change", function() {
        var data = JSON.parse($("option:selected", this).attr("data"));
        $("#name").val(data.name);
        var textarea = $("#decklist");
        var buffer = data.main.join("\n") + "\n";
        if (data.sb.length > 0) {
            buffer += "\nSideboard:\n" + data.sb.join("\n");
        }
        textarea.val(buffer);
    })
}


$(document).ready(function () {
    PD.init();
});
