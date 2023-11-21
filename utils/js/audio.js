(() => {
  const context = {
    BUFFER: null,
    getChannelData: function (e) {
      e.prototype.getChannelData = new Proxy(e.prototype.getChannelData, {
        apply(target, self, args) {
          const results_1 = Reflect.apply(target, self, args);
          //
          if (context.BUFFER !== results_1) {
            context.BUFFER = results_1;
            window.top.postMessage("audiocontext-defender-alert", "*");
            //
            for (let i = 0; i < results_1.length; i += 100) {
              let index = Math.floor(Math.random() * i);
              results_1[index] = results_1[index] + Math.random() * 0.0000001;
            }
          }
          //
          return results_1;
        },
      });
    },
    createAnalyser: function (e) {
      e.prototype.__proto__.createAnalyser = new Proxy(
        e.prototype.__proto__.createAnalyser,
        {
          apply(target, self, args) {
            const results_2 = Reflect.apply(target, self, args);
            //
            results_2.__proto__.getFloatFrequencyData = new Proxy(
              results_2.__proto__.getFloatFrequencyData,
              {
                apply(target, self, args) {
                  const results_3 = Reflect.apply(target, self, args);
                  window.top.postMessage("audiocontext-defender-alert", "*");
                  //
                  for (let i = 0; i < arguments[0].length; i += 100) {
                    let index = Math.floor(Math.random() * i);
                    arguments[0][index] =
                      arguments[0][index] + Math.random() * 0.1;
                  }
                  //
                  return results_3;
                },
              }
            );
            //
            return results_2;
          },
        }
      );
    },
  };
  //
  context.getChannelData(AudioBuffer);
  context.createAnalyser(AudioContext);
  context.createAnalyser(OfflineAudioContext);
})();
