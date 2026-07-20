// for(;;) is JS's other common "loop forever" idiom (no while-1 literal-int convention in JS).
function runAgent(client) {
  for (;;) {
    client.step();
  }
}
