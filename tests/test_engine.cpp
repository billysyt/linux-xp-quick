// SPDX-License-Identifier: MIT
// Exercise the installed librime + Lua plugin, using an isolated data directory.
#include <rime_api.h>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
RimeSessionId session;
std::string output;
struct Menu { std::vector<std::string> text; int page = 0; bool last = false; };

void expect(bool value, const std::string& label) {
  if (!value) throw std::runtime_error(label);
  std::cout << "PASS " << label << '\n';
}

void collect() {
  RIME_STRUCT(RimeCommit, commit);
  if (RimeGetCommit(session, &commit)) {
    if (commit.text) output += commit.text;
    RimeFreeCommit(&commit);
  }
}

bool key(int code, int modifiers = 0) {
  bool handled = RimeProcessKey(session, code, modifiers);
  collect();
  return handled;
}

void type(const std::string& text) { for (unsigned char c : text) key(c); }

Menu menu() {
  Menu result;
  RIME_STRUCT(RimeContext, context);
  if (RimeGetContext(session, &context)) {
    result.page = context.menu.page_no;
    result.last = context.menu.is_last_page;
    for (int i = 0; i < context.menu.num_candidates; ++i) {
      result.text.emplace_back(context.menu.candidates[i].text);
      if (context.menu.candidates[i].comment && *context.menu.candidates[i].comment)
        throw std::runtime_error(std::string("candidate has unwanted annotation: ") +
                                 context.menu.candidates[i].text + " / " + context.menu.candidates[i].comment);
    }
    RimeFreeContext(&context);
  }
  return result;
}

void clear() {
  key(0xff1b);
  RimeClearComposition(session);
  output.clear();
}

void fast_type(const std::string& keys) {
  int held = 0;
  for (unsigned char code : keys) {
    if (!key(code, code == '?' ? 1 : 0))
      output += code;  // An unhandled printable key would reach the app.
    menu();  // IBus requests the current candidates after each event.
    if (held) key(held, 1 << 30);
    held = code;
  }
  if (held) key(held, 1 << 30);
}

void run() {
  expect(RimeSelectSchema(session, "linux_xp_quick"), "schema loads");
  RimeSetOption(session, "ascii_mode", False);
  type("of");
  expect(menu().text == std::vector<std::string>{"伙","你","係","偽","氮","焦","無","絛","僚"}, "fixed 人火 1–9");
  key('2');
  expect(output == "你" && !menu().text.empty(), "OF2 commits 你 and displays predictions");
  clear(); type("oj1");
  expect(output == "什" && menu().text.at(1) == "麼", "OJ1 and visible prediction 2");
  key(0xffe1, 1); key('@', 1); key('@', 1 | (1 << 30)); key(0xffe1, 1 << 30);
  expect(output == "什麼", "Shift+2 appends exactly once");
  clear(); type("oj1"); key('2', 1);
  expect(output == "什麼", "unshifted digit keycode with Shift mask");
  clear(); type("oj1"); key(0xff1b); key('@', 1);
  expect(output.find("麼") == std::string::npos, "Escape cancels prediction");
  for (int arrow : {0xff51, 0xff53}) {
    clear(); type("oj1");
    expect(!menu().text.empty(), "prediction is visible before horizontal movement");
    expect(!key(arrow) && menu().text.empty() && output == "什",
           arrow == 0xff51 ? "Left closes prediction and reaches the application"
                            : "Right closes prediction and reaches the application");
  }
  clear(); type("oj1");
  expect(key(0xff54) && !menu().text.empty(), "Down still navigates predictions");
  expect(key(0xff52) && !menu().text.empty(), "Up still navigates predictions");
  clear(); type("oj1of2");
  expect(output == "什你", "new radicals replace prediction");
  clear(); fast_type("on4au7of2ov3km1oe7kb=9?");
  expect(output == "今晚你食左飯冇？", "unpaced overlapping key releases preserve the whole sentence");
  clear(); fast_type("ona4uo7fo2vk3mo1ek7b=9?");
  expect(output == "今晚你食左飯冇？", "an early next radical does not steal the previous selection (output: " + output + ")");
  clear(); fast_type("of2auo"); key(0xff08); key('7');
  expect(output == "你晚", "Backspace discards the early radical before selection");
  clear(); fast_type("of2auof2");
  expect(output == "你巴你", "a fourth radical continues native default selection");
  clear(); type("r ");
  expect(output == "口", "one radical + Space commits 口");
  clear(); type("rb"); auto first = menu(); key(' '); auto second = menu();
  expect(output.empty() && second.page == 1 && second.text != first.text, "two radicals + Space pages without commit");
  key('1'); expect(output == second.text.at(0), "digit selects new page");
  clear(); type("rb"); key(0xff56);
  expect(menu().text == second.text, "Space and Page Down agree");
  for (int i = 0; i < 20; ++i) key(' ');
  expect(output.empty(), "Space at final page never commits accidentally");
  clear(); type("rb"); key(0xff08); key(' ');
  expect(output == "口", "Backspace from two radicals restores one-radical Space behavior");
  clear(); type("oj1="); auto next_predictions = menu();
  key('!', 1);
  expect(output == "什" + next_predictions.text.at(0), "Shift+number follows prediction page");
  clear(); type("oj1");
  expect(RimeSelectCandidateOnCurrentPage(session, 1), "mouse selection accepted"); collect();
  expect(output == "什麼", "mouse commits only prediction tail");
  clear(); type("oj1 ");
  expect(output == "什物", "Space commits the highlighted prediction");
  clear(); type("ojo");
  expect(RimeSelectCandidateOnCurrentPage(session, 0), "mouse selection with an early radical"); collect();
  type("f2");
  expect(output == "什你", "mouse selection preserves the early radical");
  clear(); type("of9");
  expect(output == "僚", "fixed order survives prior use");
  clear();
  constexpr int caps_lock = 1 << 1;
  key(0xffe5);
  expect(!RimeGetOption(session, "ascii_mode"), "Caps Lock does not switch Quick to English");
  key('O', caps_lock); key('F', caps_lock); key('2', caps_lock);
  expect(output == "你" && !menu().text.empty(), "uppercase keycodes with Caps Lock compose and select Chinese");
  key('O', caps_lock); key('J', caps_lock); key('1', caps_lock); key('@', caps_lock | 1);
  expect(output == "你什麼", "Caps Lock works with predictions and Shift selection");
  clear(); key('K', caps_lock); key('B', caps_lock); key('=', caps_lock); key('9', caps_lock);
  expect(output == "冇", "Caps Lock works with candidate paging");
  clear();
  RimeSetOption(session, "ascii_mode", True);
  expect(!key('O', caps_lock), "English mode passes uppercase keys through");
  type("rb ");
  expect(menu().text.empty(), "ASCII mode has no Chinese candidate menu");
  RimeSetOption(session, "ascii_mode", False);
  clear(); type("oj1"); RimeSetOption(session, "ascii_mode", True);
  expect(menu().text.empty() && !key('a') && output == "什", "switching to ASCII clears the prediction marker");
  RimeSetOption(session, "ascii_mode", False);
  clear();
  auto first_session = session;
  type("oj1");
  session = RimeCreateSession();
  RimeSelectSchema(session, "linux_xp_quick");
  key('@', 1);
  expect(output.find("麼") == std::string::npos, "prediction history is isolated per session");
  RimeDestroySession(session); session = first_session;
  clear();
}
} // namespace

int main(int argc, char** argv) {
  if (argc != 3) return 2;
  RIME_STRUCT(RimeTraits, traits);
  traits.shared_data_dir = argv[2];
  traits.user_data_dir = argv[1];
  traits.app_name = "rime.linux-xp-quick-test";
  traits.log_dir = "";
  traits.min_log_level = 2;
  const char* modules[] = {"default", "plugins", "lua", nullptr};
  traits.modules = modules;
  RimeSetup(&traits); RimeInitialize(&traits);
  session = RimeCreateSession();
  int result = 0;
  try { run(); }
  catch (const std::exception& error) { std::cerr << "FAIL " << error.what() << '\n'; result = 1; }
  RimeDestroySession(session); RimeFinalize();
  return result;
}
