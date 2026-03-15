import reflex as rx

from web.components.common import _MONO
from web.mermaid import render_segment
from web.state import State

SOL_UPLOAD_ID = "sol_upload"


def _severity_badge(severity: str) -> rx.Component:
    return rx.badge(
        severity,
        color_scheme=rx.match(
            severity,
            ("pass", "green"),
            ("warning", "amber"),
            ("fail", "red"),
            ("info", "blue"),
            "gray",
        ),
        variant="soft",
        size="1",
    )


def _check_result_row(result: dict) -> rx.Component:
    return rx.box(
        rx.hstack(
            _severity_badge(result["severity"]),
            rx.badge(result["category"], color_scheme="gray", variant="outline", size="1"),
            rx.text(result["title"], size="2", font_weight="500", color="var(--gray-12)", flex="1"),
            width="100%",
            align="center",
            spacing="2",
        ),
        rx.text(result["detail"], size="1", color="var(--gray-a9)", padding_top="4px", padding_left="80px"),
        padding="10px 12px",
        border_bottom="1px solid var(--gray-a3)",
        _hover={"background": "var(--gray-a2)"},
    )


def _validate_result_row(result: dict) -> rx.Component:
    return rx.box(
        rx.hstack(
            _severity_badge(result["severity"]),
            rx.text(result["title"], size="2", font_weight="500", color="var(--gray-12)", flex="1"),
            width="100%",
            align="center",
            spacing="2",
        ),
        rx.text(result["detail"], size="1", color="var(--gray-a9)", padding_top="4px", padding_left="60px"),
        padding="10px 12px",
        border_bottom="1px solid var(--gray-a3)",
        _hover={"background": "var(--gray-a2)"},
    )


def _tab_button(label: str, tab_key: str) -> rx.Component:
    return rx.button(
        label,
        variant=rx.cond(State.sol_active_tab == tab_key, "solid", "outline"),
        color_scheme="green",
        size="2",
        on_click=State.set_sol_active_tab(tab_key),
        cursor="pointer",
    )


def _sol_check_tab() -> rx.Component:
    return rx.vstack(
        rx.cond(
            State.sol_check_error != "",
            rx.vstack(
                rx.callout(State.sol_check_error, icon="triangle_alert", color_scheme="red", size="1", width="100%"),
                rx.button(
                    rx.hstack(rx.icon("rotate-ccw", size=14), rx.text("Retry"), align="center", spacing="2"),
                    on_click=State.run_solution_check,
                    size="2",
                    variant="outline",
                    color_scheme="red",
                    cursor="pointer",
                ),
                spacing="2",
                width="100%",
            ),
        ),
        rx.cond(
            State.sol_is_checking,
            rx.center(
                rx.hstack(
                    rx.spinner(size="2"),
                    rx.text("Running checks...", size="2", color="var(--gray-a9)"),
                    spacing="2",
                    align="center",
                ),
                padding="24px",
                width="100%",
            ),
            rx.vstack(
                rx.cond(
                    State.sol_check_agent_name != "",
                    rx.hstack(
                        rx.icon("bot", size=16, color="var(--green-9)"),
                        rx.text(
                            State.sol_check_agent_name,
                            size="3",
                            font_weight="600",
                            color="var(--gray-12)",
                            font_family=_MONO,
                        ),
                        rx.text(" / ", size="2", color="var(--gray-a8)"),
                        rx.text(State.sol_check_solution_name, size="2", color="var(--gray-a9)", font_family=_MONO),
                        align="center",
                        spacing="2",
                    ),
                ),
                rx.hstack(
                    rx.badge(
                        rx.hstack(
                            rx.icon("check", size=12), rx.text(State.sol_check_pass), spacing="1", align="center"
                        ),
                        color_scheme="green",
                        variant="soft",
                        size="2",
                    ),
                    rx.badge(
                        rx.hstack(
                            rx.icon("triangle_alert", size=12),
                            rx.text(State.sol_check_warn),
                            spacing="1",
                            align="center",
                        ),
                        color_scheme="amber",
                        variant="soft",
                        size="2",
                    ),
                    rx.badge(
                        rx.hstack(
                            rx.icon("x", size=12), rx.text(State.sol_check_fail), spacing="1", align="center"
                        ),
                        color_scheme="red",
                        variant="soft",
                        size="2",
                    ),
                    rx.badge(
                        rx.hstack(rx.icon("info", size=12), rx.text(State.sol_check_info), spacing="1", align="center"),
                        color_scheme="blue",
                        variant="soft",
                        size="2",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.button(
                        "All",
                        variant=rx.cond(State.sol_check_active_category == "All", "solid", "outline"),
                        color_scheme="gray",
                        size="1",
                        on_click=State.set_sol_check_active_category("All"),
                        cursor="pointer",
                    ),
                    rx.cond(
                        State.sol_show_solution_filter,
                        rx.button(
                            "Solution",
                            variant=rx.cond(State.sol_check_active_category == "Solution", "solid", "outline"),
                            color_scheme="gray",
                            size="1",
                            on_click=State.set_sol_check_active_category("Solution"),
                            cursor="pointer",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        State.sol_show_agent_filter,
                        rx.button(
                            "Agent",
                            variant=rx.cond(State.sol_check_active_category == "Agent", "solid", "outline"),
                            color_scheme="gray",
                            size="1",
                            on_click=State.set_sol_check_active_category("Agent"),
                            cursor="pointer",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        State.sol_show_topics_filter,
                        rx.button(
                            "Topics",
                            variant=rx.cond(State.sol_check_active_category == "Topics", "solid", "outline"),
                            color_scheme="gray",
                            size="1",
                            on_click=State.set_sol_check_active_category("Topics"),
                            cursor="pointer",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        State.sol_show_knowledge_filter,
                        rx.button(
                            "Knowledge",
                            variant=rx.cond(State.sol_check_active_category == "Knowledge", "solid", "outline"),
                            color_scheme="gray",
                            size="1",
                            on_click=State.set_sol_check_active_category("Knowledge"),
                            cursor="pointer",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        State.sol_show_security_filter,
                        rx.button(
                            "Security",
                            variant=rx.cond(State.sol_check_active_category == "Security", "solid", "outline"),
                            color_scheme="gray",
                            size="1",
                            on_click=State.set_sol_check_active_category("Security"),
                            cursor="pointer",
                        ),
                        rx.fragment(),
                    ),
                    spacing="2",
                    flex_wrap="wrap",
                ),
                rx.box(
                    rx.foreach(State.sol_filtered_results, _check_result_row),
                    width="100%",
                    border="1px solid var(--gray-a4)",
                    border_radius="8px",
                    overflow="hidden",
                ),
                spacing="4",
                width="100%",
            ),
        ),
        spacing="4",
        width="100%",
    )


def _sol_validate_tab() -> rx.Component:
    return rx.vstack(
        rx.cond(
            State.sol_validate_error != "",
            rx.vstack(
                rx.callout(State.sol_validate_error, icon="triangle_alert", color_scheme="red", size="1", width="100%"),
                rx.button(
                    rx.hstack(rx.icon("rotate-ccw", size=14), rx.text("Retry"), align="center", spacing="2"),
                    on_click=State.run_solution_validate,
                    size="2",
                    variant="outline",
                    color_scheme="red",
                    cursor="pointer",
                ),
                spacing="2",
                width="100%",
            ),
        ),
        rx.cond(
            State.sol_is_validating,
            rx.center(
                rx.hstack(
                    rx.spinner(size="2"),
                    rx.text("Validating instructions...", size="2", color="var(--gray-a9)"),
                    spacing="2",
                    align="center",
                ),
                padding="24px",
                width="100%",
            ),
            rx.vstack(
                rx.cond(
                    State.sol_validate_model_display != "",
                    rx.hstack(
                        rx.icon("cpu", size=16, color="var(--green-9)"),
                        rx.text("Model: ", size="2", color="var(--gray-a9)"),
                        rx.text(
                            State.sol_validate_model_display,
                            size="2",
                            font_weight="600",
                            color="var(--gray-12)",
                            font_family=_MONO,
                        ),
                        align="center",
                        spacing="2",
                    ),
                ),
                rx.box(
                    rx.foreach(State.sol_validate_results, _validate_result_row),
                    width="100%",
                    border="1px solid var(--gray-a4)",
                    border_radius="8px",
                    overflow="hidden",
                ),
                rx.cond(
                    State.sol_validate_best_practices_md != "",
                    rx.box(
                        rx.heading(
                            "Best Practices", size="3", font_family=_MONO, color="var(--gray-12)", padding_bottom="8px"
                        ),
                        rx.foreach(State.sol_validate_bp_segments, render_segment),
                        padding_top="16px",
                    ),
                ),
                spacing="4",
                width="100%",
            ),
        ),
        spacing="4",
        width="100%",
    )


def _sol_deps_tab() -> rx.Component:
    def _deps_sort_indicator(key: str) -> rx.Component:
        return rx.cond(
            State.sol_deps_relation_sort_key == key,
            rx.icon(
                rx.cond(State.sol_deps_relation_sort_dir == "asc", "arrow-up", "arrow-down"),
                size=12,
            ),
            rx.icon("arrow-up-down", size=12),
        )

    def _deps_component_sort_indicator(key: str) -> rx.Component:
        return rx.cond(
            State.sol_deps_component_sort_key == key,
            rx.icon(
                rx.cond(State.sol_deps_component_sort_dir == "asc", "arrow-up", "arrow-down"),
                size=12,
            ),
            rx.icon("arrow-up-down", size=12),
        )

    def _deps_sortable_header(label: str, key: str) -> rx.Component:
        return rx.hstack(
            rx.text(label, font_size="11px", font_weight="700", color="var(--gray-a10)"),
            _deps_sort_indicator(key),
            spacing="1",
            align="center",
            cursor="pointer",
            on_click=State.set_sol_deps_relation_sort(key),
        )

    def _deps_component_sortable_header(label: str, key: str) -> rx.Component:
        return rx.hstack(
            rx.text(label, font_size="11px", font_weight="700", color="var(--gray-a10)"),
            _deps_component_sort_indicator(key),
            spacing="1",
            align="center",
            cursor="pointer",
            on_click=State.set_sol_deps_component_sort(key),
        )

    def _deps_relation_row(row: dict) -> rx.Component:
        return rx.grid(
            rx.text(row["dependent"], size="1", color="var(--gray-11)", font_weight="500"),
            rx.badge(row["dependent_type"], color_scheme="blue", variant="soft", size="1"),
            rx.text(row["required"], size="1", color="var(--gray-12)", font_weight="500"),
            rx.badge(row["required_type"], color_scheme="red", variant="soft", size="1"),
            rx.badge(row["source"], color_scheme="cyan", variant="soft", size="1"),
            columns="2.2fr 1fr 2.2fr 1fr 1.4fr",
            gap="10px",
            align="center",
            padding="8px 10px",
            border_bottom="1px solid var(--gray-a3)",
            width="100%",
        )

    def _deps_required_row(row: dict) -> rx.Component:
        return rx.grid(
            rx.text(row["required"], size="1", color="var(--gray-12)", font_weight="600"),
            rx.badge(row["required_type"], color_scheme="red", variant="soft", size="1"),
            rx.text(row["dependent"], size="1", color="var(--gray-a10)", font_family=_MONO),
            columns="2.6fr 1.2fr 1fr",
            gap="10px",
            align="center",
            padding="8px 10px",
            border_bottom="1px solid var(--gray-a3)",
            width="100%",
        )

    def _deps_component_row(row: dict) -> rx.Component:
        return rx.grid(
            rx.text(row["name"], size="1", color="var(--gray-12)", font_weight="600"),
            rx.text(row["schema"], size="1", color="var(--gray-a10)"),
            rx.badge(row["type"], color_scheme="blue", variant="soft", size="1"),
            rx.text(row["type_code"], size="1", color="var(--gray-a10)"),
            rx.badge(row["group"], color_scheme="gray", variant="soft", size="1"),
            rx.text(row["kind"], size="1", color="var(--gray-a10)"),
            rx.badge(row["source"], color_scheme="cyan", variant="soft", size="1"),
            columns="1.6fr 2.4fr 1.2fr 0.6fr 1fr 1.2fr 1.2fr",
            gap="10px",
            align="center",
            padding="8px 10px",
            border_bottom="1px solid var(--gray-a3)",
            width="100%",
        )

    return rx.vstack(
        rx.cond(
            State.sol_deps_error != "",
            rx.vstack(
                rx.callout(State.sol_deps_error, icon="triangle_alert", color_scheme="red", size="1", width="100%"),
                rx.button(
                    rx.hstack(rx.icon("rotate-ccw", size=14), rx.text("Retry"), align="center", spacing="2"),
                    on_click=State.run_deps_analysis,
                    size="2",
                    variant="outline",
                    color_scheme="red",
                    cursor="pointer",
                ),
                spacing="2",
                width="100%",
            ),
        ),
        rx.cond(
            State.sol_is_deps_analyzing,
            rx.center(
                rx.hstack(
                    rx.spinner(size="2"),
                    rx.text("Analysing dependencies...", size="2", color="var(--gray-a9)"),
                    spacing="2",
                    align="center",
                ),
                padding="24px",
                width="100%",
            ),
            rx.vstack(
                rx.hstack(
                    rx.icon("network", size=16, color="var(--green-9)"),
                    rx.text("Dependency Diagram", size="2", font_weight="600", color="var(--gray-12)"),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                rx.hstack(
                    rx.text("Diagram mode:", size="1", color="var(--gray-a10)", font_weight="600"),
                    rx.button(
                        "Aggregated",
                        variant=rx.cond(State.sol_deps_diagram_mode == "aggregated", "solid", "outline"),
                        size="1",
                        on_click=State.set_sol_deps_diagram_mode("aggregated"),
                    ),
                    rx.button(
                        "Detailed",
                        variant=rx.cond(State.sol_deps_diagram_mode == "detailed", "solid", "outline"),
                        size="1",
                        on_click=State.set_sol_deps_diagram_mode("detailed"),
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                rx.foreach(
                    State.sol_deps_visible_segments,
                    lambda segment: rx.cond(
                        segment["type"] == "mermaid",
                        rx.vstack(
                            rx.hstack(
                                rx.spacer(),
                                rx.button("-", on_click=State.sol_deps_zoom_out, variant="outline", size="1"),
                                rx.button("+", on_click=State.sol_deps_zoom_in, variant="outline", size="1"),
                                rx.button("Reset", on_click=State.sol_deps_zoom_reset, variant="outline", size="1"),
                                rx.badge(State.sol_deps_diagram_zoom_style, color_scheme="gray", variant="soft", size="1"),
                                spacing="2",
                                align="center",
                                width="100%",
                            ),
                            rx.box(
                                rx.el.pre(
                                    segment["content"],
                                    class_name="mermaid",
                                    width=State.sol_deps_diagram_zoom_style,
                                    min_width=State.sol_deps_diagram_zoom_style,
                                ),
                                width="100%",
                                overflow_x="auto",
                                overflow_y="auto",
                                padding="16px",
                                border="1px solid var(--gray-a4)",
                                border_radius="10px",
                                background="var(--gray-a2)",
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        render_segment(segment),
                    ),
                ),
                rx.cond(
                    (State.sol_deps_diagram_mode != "detailed") & State.sol_has_deps_relations,
                    rx.box(
                        rx.hstack(
                            rx.text("Required Components", size="2", font_weight="600"),
                            rx.spacer(),
                            rx.badge(State.sol_deps_relation_rows.length(), variant="soft", size="1"),
                            width="100%",
                            align="center",
                        ),
                        rx.text(
                            "Components required by this solution but not contained in the ZIP.",
                            size="1",
                            color="var(--gray-a10)",
                        ),
                        rx.box(
                            rx.grid(
                                rx.text("Required Component", font_size="11px", font_weight="700", color="var(--gray-a10)"),
                                rx.text("Type", font_size="11px", font_weight="700", color="var(--gray-a10)"),
                                rx.text("Dep ID", font_size="11px", font_weight="700", color="var(--gray-a10)"),
                                columns="2.6fr 1.2fr 1fr",
                                gap="10px",
                                padding="8px 10px",
                                background="var(--gray-a3)",
                            ),
                            rx.foreach(State.sol_deps_relation_rows, _deps_required_row),
                            max_height="320px",
                            overflow_y="auto",
                            border="1px solid var(--gray-a4)",
                            border_radius="10px",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    (State.sol_deps_diagram_mode != "detailed") & State.sol_has_deps_components,
                    rx.box(
                        rx.hstack(
                            rx.text("Components In Solution", size="2", font_weight="600"),
                            rx.spacer(),
                            rx.badge(State.sol_deps_filtered_component_rows.length(), variant="soft", size="1"),
                            width="100%",
                            align="center",
                        ),
                        rx.hstack(
                            rx.input(
                                placeholder="Filter by name, schema, type, code, group, kind, or source...",
                                value=State.sol_deps_component_query,
                                on_change=State.set_sol_deps_component_query,
                                size="2",
                                width="100%",
                            ),
                            rx.button("Clear", size="2", variant="outline", on_click=State.set_sol_deps_component_query("")),
                            spacing="2",
                            width="100%",
                        ),
                        rx.box(
                            rx.grid(
                                _deps_component_sortable_header("Name", "name"),
                                _deps_component_sortable_header("Schema", "schema"),
                                _deps_component_sortable_header("Type", "type"),
                                _deps_component_sortable_header("Code", "type_code"),
                                _deps_component_sortable_header("Group", "group"),
                                _deps_component_sortable_header("Detected Kind", "kind"),
                                _deps_component_sortable_header("Source", "source"),
                                columns="1.6fr 2.4fr 1.2fr 0.6fr 1fr 1.2fr 1.2fr",
                                gap="10px",
                                padding="8px 10px",
                                background="var(--gray-a3)",
                                position="sticky",
                                top="0",
                                z_index="2",
                            ),
                            rx.foreach(State.sol_deps_filtered_component_rows, _deps_component_row),
                            max_height="360px",
                            overflow_x="auto",
                            overflow_y="auto",
                            border="1px solid var(--gray-a4)",
                            border_radius="10px",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    (State.sol_deps_diagram_mode != "detailed") & State.sol_has_deps_relations,
                    rx.box(
                        rx.hstack(
                            rx.text("Dependency Relations Table", size="2", font_weight="600"),
                            rx.spacer(),
                            rx.badge(State.sol_deps_filtered_relation_rows.length(), variant="soft", size="1"),
                            width="100%",
                            align="center",
                        ),
                        rx.hstack(
                            rx.input(
                                placeholder="Filter by dependent, required, type, or source...",
                                value=State.sol_deps_relation_query,
                                on_change=State.set_sol_deps_relation_query,
                                size="2",
                                width="100%",
                            ),
                            rx.button("Clear", size="2", variant="outline", on_click=State.set_sol_deps_relation_query("")),
                            spacing="2",
                            width="100%",
                        ),
                        rx.box(
                            rx.grid(
                                _deps_sortable_header("Dependent", "dependent"),
                                _deps_sortable_header("Type", "dependent_type"),
                                _deps_sortable_header("Required", "required"),
                                _deps_sortable_header("Type", "required_type"),
                                _deps_sortable_header("Source", "source"),
                                columns="2.2fr 1fr 2.2fr 1fr 1.4fr",
                                gap="10px",
                                padding="8px 10px",
                                background="var(--gray-a3)",
                            ),
                            rx.foreach(State.sol_deps_filtered_relation_rows, _deps_relation_row),
                            max_height="420px",
                            overflow_y="auto",
                            border="1px solid var(--gray-a4)",
                            border_radius="10px",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                spacing="4",
                width="100%",
            ),
        ),
        spacing="4",
        width="100%",
    )


def _sol_rename_tab() -> rx.Component:
    return rx.vstack(
        rx.cond(
            State.sol_detected_info.length() > 0,  # type: ignore
            rx.callout(
                rx.vstack(
                    rx.text("Detected from solution:", size="2", font_weight="500"),
                    rx.text(
                        rx.text.strong("Agent: "),
                        State.sol_detected_info["bot_display_name"],
                        size="1",
                        color="var(--gray-a9)",
                    ),
                    rx.text(
                        rx.text.strong("Solution: "),
                        State.sol_detected_info["solution_unique_name"],
                        size="1",
                        color="var(--gray-a9)",
                    ),
                    spacing="1",
                ),
                icon="info",
                color_scheme="blue",
                size="1",
                width="100%",
            ),
        ),
        rx.vstack(
            rx.text("New Agent Name", size="2", font_weight="500", color="var(--gray-11)"),
            rx.input(
                placeholder="My Renamed Agent",
                value=State.sol_rename_new_agent,
                on_change=State.set_sol_rename_new_agent,
                width="100%",
                size="2",
                font_family=_MONO,
            ),
            rx.text("Display name for the agent", size="1", color="var(--gray-a8)"),
            spacing="1",
            width="100%",
        ),
        rx.vstack(
            rx.text("New Solution Name", size="2", font_weight="500", color="var(--gray-11)"),
            rx.input(
                placeholder="MyRenamedSolution",
                value=State.sol_rename_new_solution,
                on_change=State.set_sol_rename_new_solution,
                width="100%",
                size="2",
                font_family=_MONO,
            ),
            rx.text("PascalCase, letters/digits/underscores only (e.g. MyNewBot)", size="1", color="var(--gray-a8)"),
            spacing="1",
            width="100%",
        ),
        rx.cond(
            State.sol_rename_error != "",
            rx.vstack(
                rx.callout(State.sol_rename_error, icon="triangle_alert", color_scheme="red", size="1", width="100%"),
                rx.button(
                    rx.hstack(rx.icon("rotate-ccw", size=14), rx.text("Retry"), align="center", spacing="2"),
                    on_click=State.run_rename,
                    size="2",
                    variant="outline",
                    color_scheme="red",
                    cursor="pointer",
                ),
                spacing="2",
                width="100%",
            ),
        ),
        rx.button(
            rx.cond(
                State.sol_is_renaming,
                rx.hstack(rx.spinner(size="1"), rx.text("Renaming..."), align="center", spacing="2"),
                rx.hstack(rx.icon("pen-line", size=15), rx.text("Rename Solution"), align="center", spacing="2"),
            ),
            on_click=State.run_rename,
            width="100%",
            size="3",
            color_scheme="green",
            disabled=State.sol_is_renaming,
            cursor="pointer",
            font_weight="500",
        ),
        rx.cond(
            State.sol_rename_result.length() > 0,  # type: ignore
            rx.vstack(
                rx.callout(
                    rx.vstack(
                        rx.text("Rename complete!", size="2", font_weight="600", color="var(--green-11)"),
                        rx.text(
                            rx.text.strong("Agent: "),
                            State.sol_rename_result["old_agent_name"],
                            " -> ",
                            State.sol_rename_result["new_agent_name"],
                            size="1",
                        ),
                        rx.text(
                            rx.text.strong("Solution: "),
                            State.sol_rename_result["old_solution_name"],
                            " -> ",
                            State.sol_rename_result["new_solution_name"],
                            size="1",
                        ),
                        rx.text(
                            rx.text.strong("Files modified: "),
                            State.sol_rename_result["files_modified"].to(str),
                            " | Folders renamed: ",
                            State.sol_rename_result["folders_renamed"].to(str),
                            size="1",
                        ),
                        spacing="1",
                    ),
                    icon="check",
                    color_scheme="green",
                    size="1",
                    width="100%",
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("download", size=15), rx.text("Download Renamed ZIP"), align="center", spacing="2"
                    ),
                    on_click=State.download_renamed_zip,
                    width="100%",
                    size="3",
                    color_scheme="green",
                    variant="outline",
                    cursor="pointer",
                    font_weight="500",
                ),
                spacing="3",
                width="100%",
            ),
        ),
        spacing="4",
        width="100%",
    )


def solution_tools_form() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.vstack(
                rx.heading(
                    "Solution Tools",
                    size="7",
                    font_family=_MONO,
                    font_weight="600",
                    color="var(--gray-12)",
                    letter_spacing="-0.5px",
                ),
                rx.text(
                    "Check, validate, analyse dependencies, or rename a Power Platform solution ZIP",
                    size="2",
                    color="var(--gray-a9)",
                    text_align="center",
                ),
                spacing="2",
                align="center",
            ),
            rx.box(
                rx.vstack(
                    rx.cond(
                        State.sol_has_zip,
                        rx.hstack(
                            rx.icon("file-archive", size=16, color="var(--green-9)"),
                            rx.text(State.sol_zip_name, size="2", font_family=_MONO, color="var(--gray-11)", flex="1"),
                            rx.button(
                                rx.icon("x", size=14),
                                variant="ghost",
                                size="1",
                                color_scheme="gray",
                                on_click=State.sol_clear,
                                cursor="pointer",
                            ),
                            width="100%",
                            align="center",
                            padding="8px 12px",
                            background="var(--green-a2)",
                            border="1px solid var(--green-a5)",
                            border_radius="8px",
                        ),
                        rx.vstack(
                            rx.upload(
                                rx.vstack(
                                    rx.box(
                                        rx.icon("upload", size=28, color="var(--green-9)"),
                                        padding="14px",
                                        background="var(--green-a3)",
                                        border_radius="50%",
                                        border="1px solid var(--green-a5)",
                                        display="inline-flex",
                                    ),
                                    rx.text(
                                        "Drop a solution ZIP (.zip) or click to browse",
                                        size="3",
                                        color="var(--gray-11)",
                                        font_weight="500",
                                    ),
                                    rx.text("Power Platform solution export (.zip)", size="2", color="var(--gray-a8)"),
                                    align="center",
                                    spacing="3",
                                ),
                                id=SOL_UPLOAD_ID,
                                border="1.5px dashed var(--green-a6)",
                                border_radius="12px",
                                padding="48px 32px",
                                width="100%",
                                cursor="pointer",
                                multiple=False,
                                accept={".zip": ["application/zip"]},
                                background="var(--green-a1)",
                                transition="all 0.15s ease",
                            ),
                            rx.cond(
                                rx.selected_files(SOL_UPLOAD_ID).length() > 0,
                                rx.box(
                                    rx.vstack(
                                        rx.hstack(
                                            rx.icon("check", size=14, color="var(--green-9)"),
                                            rx.text("File ready to upload", size="2", color="var(--green-11)"),
                                            align="center",
                                            spacing="2",
                                        ),
                                        rx.foreach(
                                            rx.selected_files(SOL_UPLOAD_ID),
                                            lambda f: rx.hstack(
                                                rx.icon("file", size=12, color="var(--green-9)"),
                                                rx.text(f, size="1", color="var(--gray-a10)", font_family=_MONO),
                                                spacing="1",
                                                align="center",
                                            ),
                                        ),
                                        spacing="2",
                                        width="100%",
                                    ),
                                    width="100%",
                                    padding="10px 12px",
                                    background="var(--green-a2)",
                                    border="1px solid var(--green-a5)",
                                    border_radius="8px",
                                ),
                                rx.fragment(),
                            ),
                            rx.button(
                                rx.hstack(
                                    rx.icon("zap", size=15), rx.text("Upload & Analyse"), align="center", spacing="2"
                                ),
                                on_click=State.handle_solution_upload(rx.upload_files(upload_id=SOL_UPLOAD_ID)),
                                width="100%",
                                size="3",
                                color_scheme="green",
                                disabled=rx.selected_files(SOL_UPLOAD_ID).length() == 0,
                                cursor="pointer",
                                font_weight="500",
                            ),
                            spacing="4",
                            width="100%",
                        ),
                    ),
                    rx.cond(
                        State.sol_has_zip,
                        rx.vstack(
                            rx.separator(size="4"),
                            rx.hstack(
                                _tab_button("Check", "check"),
                                rx.cond(
                                    State.sol_has_agent_assets,
                                    _tab_button("Validate", "validate"),
                                    rx.fragment(),
                                ),
                                _tab_button("Dependencies", "deps"),
                                rx.cond(
                                    State.sol_has_agent_assets,
                                    _tab_button("Rename", "rename"),
                                    rx.fragment(),
                                ),
                                spacing="2",
                                flex_wrap="wrap",
                            ),
                            rx.match(
                                State.sol_active_tab,
                                ("check", _sol_check_tab()),
                                ("validate", rx.cond(State.sol_has_agent_assets, _sol_validate_tab(), _sol_check_tab())),
                                ("deps", _sol_deps_tab()),
                                (
                                    "rename",
                                    rx.cond(State.sol_has_agent_assets, _sol_rename_tab(), _sol_check_tab()),
                                ),
                                _sol_check_tab(),
                            ),
                            spacing="4",
                            width="100%",
                        ),
                    ),
                    spacing="4",
                    width="100%",
                ),
                padding="28px",
                background="var(--gray-a2)",
                border="1px solid var(--gray-a4)",
                border_radius="16px",
                max_width="800px",
                width="100%",
                box_shadow="0 8px 32px rgba(0,0,0,0.35)",
            ),
            spacing="6",
            align="center",
            width="100%",
        ),
        width="100%",
        padding="64px 24px",
        min_height="calc(100vh - 54px)",
    )
