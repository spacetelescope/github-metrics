<template>
  <div class="content">
    <h1 class="header has-text-left"> Limit aggregate stats by dates </h1>
    <input :class="classObject" type="range" :min="min" v-model="scaledValue" :max="max" :step="step" :name="name" :orient="vertical && 'vertical'" :disabled="disabled" number>
  </div>
</template>

<script>
export default {
  props: {
    value: String,
    type: String,
    name: String,
    size: String,
    isFullwidth: Boolean,
    disabled: Boolean,
    // orientation:
    vertical: Boolean
  },
  computed: {
    min: {
      get: function () {
        return 0;
      },
    },
    max: {
      get: function () {
        return 100;
      },
    },
    step: {
      get: function () {
        return 1;
      },
    },
    scaledValue: {
      get: function () {
        // Convert Datetime to int between 0 - 100
        return 45;
        // return this.value;
      },
      set: function (val) {
        // eslint-disable-next-line
        console.log('val', val)
      }
      // set: function (val) {
      //   // Convert int between 0 - 100 to Datetime
      //   // this.value = val;
      // },
    },
    low () {
      return '0%'
    },
    high () {
      return (this.realValue - this.min) / (this.max - this.min) * 100 + '%'
    },
    classObject () {
      const { type, size, isFullwidth } = this
      return {
        slider: true,
        [`is-${type}`]: type,
        [`is-${size}`]: size,
        'is-fullwidth': isFullwidth
      }
    },
  },
  beforeMount () {
    if (this.max < this.min) {
      throw 'Unexpected range setting: Maximum cannot be less than minimum'
    }

    this.update(this.value)
  },

  mounted () {
    this.$el.style.setProperty('--low', this.low)
    this.$el.style.setProperty('--high', this.high)
  },

  watch: {
    realValue (newVal, oldVal) {
      if (Number(newVal) !== Number(oldVal)) {
        this.$el.style.setProperty('--high', this.high)
        this.$emit('change', newVal)
      }
    },
    value (val) {
      this.update(val)
    }
  },

  methods: {
    update (val) {
      if (val > this.max) {
        this.realValue = this.max
      } else if (val < this.min) {
        this.realValue = this.min
      } else {
        this.realValue = val
      }
    }
  },
}
</script>

<style lang="scss">
@import '~bulma/sass/utilities/functions';

$border: '1px';
$custom-colors: null !default;
$text: hsl(0, 0%, 29%);
$white: hsl(0, 0%, 100%) !default;
$black: hsl(0, 0%, 4%) !default;
$cyan: hsl(204, 71%,  53%) !default;
$green: hsl(141, 53%,  53%) !default;
$yellow: hsl(48,  100%, 67%) !default;
$red: hsl(348, 86%, 61%) !default;
$warning: $yellow !default;
$warning-invert: findColorInvert($warning);
$warning-dark: findColorDark($warning);
$warning-light: findColorLight($warning);
$danger: $red !default;
$danger-invert: findColorInvert($danger);
$danger-dark: findColorDark($danger);
$danger-light: findColorLight($danger);
$success: $green !default;
$success-invert: findColorInvert($success);
$success-dark: findColorDark($success);
$success-light: findColorLight($success);
$info: $cyan !default;
$info-invert: findColorInvert($info);
$info-dark: findColorDark($info);
$info-light: findColorLight($info);
$white-ter: hsl(0, 0%, 96%) !default;
$light: $white-ter !default;
$grey-darker: hsl(0, 0%, 21%) !default;
$dark: $grey-darker !default;
$blue: hsl(217, 71%,  53%) !default;
$link: $blue !default;
$link-dark: findDarkColor($link) !default;
$turquoise: hsl(171, 100%, 41%) !default;
$primary: $turquoise !default;
$primary-light: findLightColor($primary) !default;
$primary-dark: findDarkColor($primary) !default;
$light-invert: findColorInvert($light) !default;
$dark-invert: findColorInvert($dark) !default;
$link-invert: findColorInvert($link) !default;
$link-light: findLightColor($link) !default;
$primary-invert: findColorInvert($primary) !default;
$colors: mergeColorMaps(("white": ($white, $black), "black": ($black, $white), "light": ($light, $light-invert), "dark": ($dark, $dark-invert), "primary": ($primary, $primary-invert, $primary-light, $primary-dark), "link": ($link, $link-invert, $link-light, $link-dark), "info": ($info, $info-invert, $info-light, $info-dark), "success": ($success, $success-invert, $success-light, $success-dark), "warning": ($warning, $warning-invert, $warning-light, $warning-dark), "danger": ($danger, $danger-invert, $danger-light, $danger-dark)), $custom-colors) !default;

input[type=range].slider {
  $radius: 290486px;
  --height: 8px;

  &.is-small {
    --height: 4px;
  }
  &.is-medium {
    --height: 12px;
  }
  &.is-large {
    --height: 16px;
  }

  &.is-fullwidth {
    width: 100%;
  }

  border: none;
  border-radius: $radius;
  display: block;
  height: var(--height);
  padding: 0;
  margin: 0;
  // width: 100%;
  cursor: pointer;
  outline: none;
  background: $border;
  -webkit-tap-highlight-color: transparent;

  &:focus {
    outline: none;
  }
  // http://stackoverflow.com/questions/18794026/remove-dotted-outline-from-range-input-element-in-firefox
  &::-moz-focus-outer {
    border: none;
  }

  &::-webkit-slider-runnable-track,
  &::-webkit-slider-thumb,
  & {
    appearance: none;
  }

  @mixin thumb-base() {
    border-radius: 50%;
    height: calc(var(--height) * 2.33);
    width: calc(var(--height) * 2.33);
    background-color: #FFF;
    border: calc(var(--height) / 2) solid $text;
    box-shadow: 0 2px 3px rgba(17, 17, 17, 0.1);
    transform: translateZ(0);
    transition: (0.233s / 2) ease-in-out;
    box-sizing: border-box;

    &:hover {
      transform: scale(1.25);
    }
  }

  @mixin thumb-base-active {
    cursor: grabbing;
  }

  @mixin track {
    display: flex;
    align-items: center;
    height: var(--height);
    border-radius: $radius;
    --track-background: linear-gradient(to right, transparent var(--low), $text calc(0%), $text var(--high), transparent calc(0%)) no-repeat 0 100%;
    background: var(--track-background);
    transform: translateZ(0);
    transition: (0.233s / 2);
  }

  &::-webkit-slider-thumb {
    @include thumb-base();
    &:active {
      @include thumb-base-active();
    }
  }
  &::-webkit-slider-runnable-track {
    @include track();
  }

  &::-moz-range-thumb {
    @include thumb-base();
    &:active {
      @include thumb-base-active();
    }
  }
  &::-moz-range-progress:focus {
    outline: 0;
    border: 0;
  }
  &::-moz-range-track {
    background: transparent;
  }
  &::-moz-range-progress {
    display: flex;
    align-items: center;
    width: 100%;
    height: var(--height);
    border-radius: $radius;
    background-color: $text;
  }

  &::-ms-thumb {
    @include thumb-base();
    &:active {
      @include thumb-base-active();
    }
  }
  &::-ms-tooltip {
    display:none;
  }

  // Colors
  @each $name, $pair in $colors {
    $color: nth($pair, 1);
    &.is-#{$name} {
      &::-webkit-slider-thumb {
        border-color: $color;
      }
      &::-webkit-slider-runnable-track {
        --track-background: linear-gradient(to right, transparent var(--low), $color calc(0%),  $color var(--high), transparent calc(0%)) no-repeat 0 100%;
        background: var(--track-background);
      }
      // http://www.quirksmode.org/blog/archives/2015/11/styling_and_scr.html
      &::-moz-range-thumb {
        border-color: $color;
      }
      &::-moz-range-progress {
        background-color: $color;
      }
      &::-ms-thumb {
        border-color: $color;
      }
      &::-ms-fill-lower {
        background-color: $color;
      }
    }
  }

  &[orient=vertical] {
    writing-mode: bt-lr; // IE
    -webkit-appearance: slider-vertical;  // webkit
    height: 200px;
    width: var(--height);
    -webkit-transform-origin: 0 0;
    position: relative;
    top: 0;
    left: 0;

    // Colors
    @each $name, $pair in $colors {
      $color: nth($pair, 1);
      &.is-#{$name} {
        &::-webkit-slider-thumb {
          &:after {
            width: 50px;
            height: 50px;
            background-color: red;
            border: 2px solid $color;
            content: '';
            position: absolute;
            z-index: 233;
          }
        }
        &::-webkit-slider-runnable-track {
          display: block;
          --track-background: linear-gradient(to top, transparent var(--low), $color 0,  $color var(--high), transparent 0) no-repeat 0 100%;
          background: var(--track-background);
        }
      }
    }
  }

}
</style>
