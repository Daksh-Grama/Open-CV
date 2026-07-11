"""AstroSurfer - entry point, game loop, and state machine.

The loop is written with async/await so this file can later be shipped to
a browser via `pygbag main.py` (see README) with no changes; run normally
with `python main.py`, it behaves exactly like a regular desktop game.
"""

import asyncio
import os

import pygame

import settings as s
import profile as profile_mod
import ui
from level import Level, features_used, FEATURE_LABELS
from levels import LEVELS, TUTORIAL

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "assets", "audio")


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass

        self.screen = pygame.display.set_mode((s.SCREEN_W, s.SCREEN_H))
        pygame.display.set_caption(s.TITLE)
        self.clock = pygame.time.Clock()

        self.profiles_data = profile_mod.load_profiles()
        profile_mod.migrate_legacy_scores_if_needed(self.profiles_data)
        self.profile = None

        self.state = "PROFILE_SELECT"
        self.level_index = None          # int index into LEVELS, or "tutorial"
        self.current_level = None
        self.last_result_new_best = False
        self.feature_banner_text = None
        self.feature_banner_timer = 0.0

        self.profile_menu = ui.Menu([])
        self.name_input = ui.TextInput()
        self.main_menu = ui.Menu(["Start", "Shop", "Switch Profile", "Quit"])
        self.level_select_menu = ui.Menu([])
        self.pause_menu = ui.Menu(["Resume", "Restart Run", "Level Select"])
        self.game_over_menu = ui.Menu(["Retry", "Level Select"])
        self.complete_menu = ui.Menu([])
        self.no_lives_menu = ui.Menu([])
        self.shop_menu = ui.Menu([])
        self._shop_ids = []
        self.confirm_delete_menu = ui.Menu(["No, keep this profile", "Yes, delete permanently"])
        self._pending_delete_name = None

        self.refresh_profile_menu()
        self.running = True

    def _save_profile(self):
        profile_mod.save_profiles(self.profiles_data)

    # -- profile lifecycle ----------------------------------------------------
    def refresh_profile_menu(self):
        names = profile_mod.list_profile_names(self.profiles_data)
        self.profile_menu.set_options(names + ["+ New Profile"])

    def _on_profile_select(self, label):
        if label == "+ New Profile":
            self.name_input = ui.TextInput()
            pygame.key.start_text_input()
            self.state = "NAME_ENTRY"
            return
        self._activate_profile(label)

    def _handle_profile_select_input(self, event):
        if event.key == pygame.K_UP:
            self.profile_menu.navigate(-1)
        elif event.key == pygame.K_DOWN:
            self.profile_menu.navigate(1)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self._on_profile_select(self.profile_menu.selected_label())
        elif event.key == pygame.K_DELETE:
            label = self.profile_menu.selected_label()
            if label != "+ New Profile":
                self._pending_delete_name = label
                self.confirm_delete_menu.set_options(["No, keep this profile", "Yes, delete permanently"])
                self.state = "CONFIRM_DELETE"

    def _on_confirm_delete(self, label):
        if label.startswith("Yes") and self._pending_delete_name:
            profile_mod.delete_profile(self.profiles_data, self._pending_delete_name)
        self._pending_delete_name = None
        self.refresh_profile_menu()
        self.state = "PROFILE_SELECT"

    def _activate_profile(self, name):
        self.profile = profile_mod.get_profile(self.profiles_data, name)
        self.profiles_data["last_active"] = name
        self._save_profile()
        if not self.profile["tutorial_completed"]:
            self.start_tutorial()
        else:
            self.state = "MENU"

    def _confirm_name_entry(self):
        name = self.name_input.buffer.strip()
        if not name:
            return
        pygame.key.stop_text_input()
        if profile_mod.get_profile(self.profiles_data, name) is None:
            profile_mod.create_profile(self.profiles_data, name)
        self._activate_profile(name)

    # -- level lifecycle -----------------------------------------------------
    def refresh_level_select(self):
        t_entry = self.profile["levels"].get(TUTORIAL.KEY, {})
        options = [("Tutorial", "Replay the tutorial" + ("  - COMPLETE" if t_entry.get("completed") else ""))]
        last_key = self.profile.get("last_level_key")
        resume_index = 0
        for i, module in enumerate(LEVELS):
            entry = self.profile["levels"].get(module.KEY, {})
            best = entry.get("best_pct", 0.0)
            done = "  - COMPLETE" if entry.get("completed") else ""
            options.append((module.NAME, f"BPM {module.BPM}   Best {best:.0f}%{done}"))
            if module.KEY == last_key:
                resume_index = i + 1  # +1 to account for the "Tutorial" entry at index 0
        self.level_select_menu.set_options(options)
        self.level_select_menu.selected = resume_index

    def _equipped_colors(self):
        equipped = self.profile["cosmetics_equipped"]
        skin = profile_mod.COSMETICS.get(equipped.get("skin"), {}).get("color")
        death_fx = profile_mod.COSMETICS.get(equipped.get("death_fx"), {}).get("color")
        return skin, death_fx

    def start_tutorial(self):
        self.level_index = "tutorial"
        self._begin_level(TUTORIAL)

    def try_start_level(self, index):
        self.level_index = index
        module = LEVELS[index]
        if profile_mod.consume_life(self.profile):
            self.profile["last_level_key"] = module.KEY
            self._save_profile()
            self._begin_level(module)
        else:
            self._save_profile()
            self.no_lives_menu.set_options(["Refill (150 Shards)", "Back to Level Select"])
            self.state = "NO_LIVES"

    def _begin_level(self, module):
        skin_color, death_fx_color = self._equipped_colors()
        self.current_level = Level(module, skin_color=skin_color, death_fx_color=death_fx_color)
        self.state = "PLAYING"
        self._play_music(module.KEY)

        self.feature_banner_text = None
        self.feature_banner_timer = 0.0
        if module is not TUTORIAL:
            newly_seen = [f for f in features_used(module) if profile_mod.mark_feature_seen(self.profile, f)]
            if newly_seen:
                self.feature_banner_text = ", ".join(FEATURE_LABELS[f] for f in newly_seen)
                self.feature_banner_timer = ui.FEATURE_BANNER_DURATION
                self._save_profile()

    def _play_music(self, key):
        if not pygame.mixer.get_init():
            return
        path = os.path.join(AUDIO_DIR, f"{key}.wav")
        if not os.path.exists(path):
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loops=-1)
        except pygame.error:
            pass

    def _stop_music(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()

    def _pause_music(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.pause()

    def _unpause_music(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.unpause()

    # -- shop ------------------------------------------------------------------
    def refresh_shop_menu(self):
        options = []
        self._shop_ids = []
        for cid, item in profile_mod.COSMETICS.items():
            owned = cid in self.profile["cosmetics_owned"]
            equipped = self.profile["cosmetics_equipped"].get(item["category"]) == cid
            if item.get("price_usd") is not None:
                price = f"${item['price_usd']:.2f} (real-money stub)"
            else:
                price = "Free" if item["price_shards"] == 0 else f"{item['price_shards']} Shards"
            status = " (equipped)" if equipped else (" (owned)" if owned else "")
            options.append((f"{item['name']}{status}", f"{item['category']} - {price}"))
            self._shop_ids.append(cid)
        self.shop_menu.set_options(options)

    def _on_shop_confirm(self):
        if not self._shop_ids:
            return
        keep_selected = self.shop_menu.selected
        cid = self._shop_ids[keep_selected]
        item = profile_mod.COSMETICS[cid]
        if cid not in self.profile["cosmetics_owned"]:
            pay_with = "usd" if item.get("price_usd") is not None else "shards"
            profile_mod.buy_cosmetic(self.profile, cid, pay_with=pay_with)
        # buying (or re-selecting an already-owned item) equips it - a
        # cosmetic you just bought and can't wear isn't much of a purchase
        if cid in self.profile["cosmetics_owned"]:
            profile_mod.equip_cosmetic(self.profile, cid)
        self._save_profile()
        self.refresh_shop_menu()
        self.shop_menu.selected = keep_selected

    # -- input -----------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        if self.state == "NAME_ENTRY":
            self._handle_name_entry_input(event)
            return

        if event.type != pygame.KEYDOWN:
            return

        if self.state == "PROFILE_SELECT":
            self._handle_profile_select_input(event)
        elif self.state == "CONFIRM_DELETE":
            self._menu_input(event, self.confirm_delete_menu, self._on_confirm_delete, allow_escape=True,
                              escape_action=lambda: self._on_confirm_delete("No"))
        elif self.state == "MENU":
            self._menu_input(event, self.main_menu, self._on_main_menu, allow_escape=False)
        elif self.state == "LEVEL_SELECT":
            self._menu_input(event, self.level_select_menu, self._on_level_select, allow_escape=True)
        elif self.state == "SHOP":
            self._handle_shop_input(event)
        elif self.state == "PLAYING":
            self._playing_input(event)
        elif self.state == "PAUSED":
            self._menu_input(event, self.pause_menu, self._on_pause, allow_escape=True, escape_action=self._on_pause_resume)
        elif self.state == "GAME_OVER":
            self._menu_input(event, self.game_over_menu, self._on_game_over, allow_escape=False)
        elif self.state == "LEVEL_COMPLETE":
            self._menu_input(event, self.complete_menu, self._on_complete, allow_escape=False)
        elif self.state == "NO_LIVES":
            self._menu_input(event, self.no_lives_menu, self._on_no_lives, allow_escape=True, escape_action=self._back_to_level_select)

    def _handle_name_entry_input(self, event):
        if event.type == pygame.TEXTINPUT:
            self.name_input.handle_text(event.text)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.name_input.backspace()
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._confirm_name_entry()
            elif event.key == pygame.K_ESCAPE:
                pygame.key.stop_text_input()
                self.refresh_profile_menu()
                self.state = "PROFILE_SELECT"

    def _handle_shop_input(self, event):
        if event.key == pygame.K_UP:
            self.shop_menu.navigate(-1)
        elif event.key == pygame.K_DOWN:
            self.shop_menu.navigate(1)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self._on_shop_confirm()
        elif event.key == pygame.K_ESCAPE:
            self.state = "MENU"

    def _menu_input(self, event, menu, on_confirm, allow_escape, escape_action=None):
        if event.key == pygame.K_UP:
            menu.navigate(-1)
        elif event.key == pygame.K_DOWN:
            menu.navigate(1)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            on_confirm(menu.selected_label())
        elif event.key == pygame.K_ESCAPE and allow_escape:
            (escape_action or self._go_to_main_menu)()

    def _go_to_main_menu(self):
        self.state = "MENU"

    def _back_to_level_select(self):
        self.refresh_level_select()
        self.state = "LEVEL_SELECT"

    def _playing_input(self, event):
        if event.key in (pygame.K_SPACE, pygame.K_UP):
            if self.current_level.pending_popup:
                self.current_level.dismiss_popup()
            else:
                self.current_level.handle_jump_press()
        elif event.key == pygame.K_ESCAPE:
            self._pause_music()
            self.state = "PAUSED"

    # -- menu confirm handlers ---------------------------------------------------
    def _on_main_menu(self, label):
        if label == "Start":
            self._back_to_level_select()
        elif label == "Shop":
            self.refresh_shop_menu()
            self.state = "SHOP"
        elif label == "Switch Profile":
            self.refresh_profile_menu()
            self.state = "PROFILE_SELECT"
        elif label == "Quit":
            self.running = False

    def _on_level_select(self, label):
        if label == "Tutorial":
            self.start_tutorial()
            return
        for i, module in enumerate(LEVELS):
            if module.NAME == label:
                self.try_start_level(i)
                return

    def _on_pause_resume(self):
        self._unpause_music()
        self.state = "PLAYING"

    def _on_pause(self, label):
        if label == "Resume":
            self._on_pause_resume()
        elif label == "Restart Run":
            module = TUTORIAL if self.level_index == "tutorial" else LEVELS[self.level_index]
            self._begin_level(module)
        elif label == "Level Select":
            self._stop_music()
            self._back_to_level_select()

    def _on_game_over(self, label):
        if label == "Retry":
            if self.level_index == "tutorial":
                self.start_tutorial()
            else:
                self.try_start_level(self.level_index)
        else:
            self._stop_music()
            self._back_to_level_select()

    def _on_complete(self, label):
        if label == "Next Level":
            self.try_start_level(self.level_index + 1)
        elif label == "Retry":
            if self.level_index == "tutorial":
                self.start_tutorial()
            else:
                self.try_start_level(self.level_index)
        else:
            self._stop_music()
            self._back_to_level_select()

    def _on_no_lives(self, label):
        if label.startswith("Refill"):
            if profile_mod.refill_lives_with_currency(self.profile):
                self._save_profile()
                self.try_start_level(self.level_index)
        else:
            self._back_to_level_select()

    # -- simulation ----------------------------------------------------------------
    def update(self, dt):
        if self.feature_banner_timer > 0:
            self.feature_banner_timer = max(0.0, self.feature_banner_timer - dt)

        if self.state == "PLAYING":
            self.current_level.update(dt)
            if self.current_level.state == "dead":
                self._finish_attempt(completed=False)
            elif self.current_level.state == "complete":
                self._finish_attempt(completed=True)
        elif self.state in ("GAME_OVER", "LEVEL_COMPLETE") and self.current_level:
            # let the death-burst / shake / trail particles finish animating over the overlay
            self.current_level.particles.update(dt)
            self.current_level.surfer.tick_shake(dt)

    def _finish_attempt(self, completed):
        level = self.current_level
        self.last_result_new_best = profile_mod.record_attempt(
            self.profile, level.key, level.progress if not completed else 1.0, completed, level.score
        )
        if level.key == TUTORIAL.KEY and completed:
            self.profile["tutorial_completed"] = True
        self._save_profile()
        self._stop_music()

        if completed:
            has_next = self.level_index != "tutorial" and self.level_index + 1 < len(LEVELS)
            options = (["Next Level"] if has_next else []) + ["Retry", "Level Select"]
            self.complete_menu.set_options(options)
            self.state = "LEVEL_COMPLETE"
        else:
            self.state = "GAME_OVER"

    # -- rendering -------------------------------------------------------------------
    def draw(self):
        if self.state == "PROFILE_SELECT":
            ui.draw_profile_select(self.screen, self.profile_menu)
        elif self.state == "CONFIRM_DELETE":
            pending = profile_mod.get_profile(self.profiles_data, self._pending_delete_name)
            ui.draw_confirm_delete(self.screen, self.confirm_delete_menu, pending)
        elif self.state == "NAME_ENTRY":
            self.name_input.draw(self.screen, "NAME YOUR PROFILE", "Letters, numbers, spaces, - and _")
        elif self.state == "MENU":
            ui.draw_main_menu(self.screen, self.main_menu, self.profile)
        elif self.state == "LEVEL_SELECT":
            ui.draw_level_select(self.screen, self.level_select_menu)
        elif self.state == "SHOP":
            ui.draw_shop(self.screen, self.shop_menu, self.profile)
        elif self.state == "PLAYING":
            self.current_level.draw(self.screen)
            ui.draw_hud(self.screen, self.current_level, self.profile)
            ui.draw_feature_banner(self.screen, self.feature_banner_text, self.feature_banner_timer)
            if self.current_level.pending_popup:
                ui.draw_tutorial_popup(self.screen, self.current_level.pending_popup)
        elif self.state == "PAUSED":
            self.current_level.draw(self.screen)
            ui.draw_hud(self.screen, self.current_level, self.profile)
            ui.draw_pause(self.screen, self.pause_menu)
        elif self.state == "GAME_OVER":
            self.current_level.draw(self.screen)
            ui.draw_game_over(
                self.screen, self.game_over_menu, self.current_level.progress * 100,
                self.last_result_new_best, self.profile["lives"], self.profile["currency"],
            )
        elif self.state == "LEVEL_COMPLETE":
            self.current_level.draw(self.screen)
            ui.draw_level_complete(
                self.screen, self.complete_menu, self.last_result_new_best,
                self.current_level.score, self.profile["lives"], self.profile["currency"],
            )
        elif self.state == "NO_LIVES":
            if self.current_level:
                self.current_level.draw(self.screen)
            ui.draw_no_lives(self.screen, self.no_lives_menu, self.profile, profile_mod.LIFE_REFILL_COST)

        pygame.display.flip()


async def main():
    game = Game()
    while game.running:
        dt = game.clock.tick(s.FPS) / 1000.0
        dt = min(dt, 1 / 30)  # guard against huge steps after a stall/alt-tab

        for event in pygame.event.get():
            game.handle_event(event)

        game.update(dt)
        game.draw()

        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
