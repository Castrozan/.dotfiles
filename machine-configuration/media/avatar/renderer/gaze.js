const GAZE_FOLLOW_RATE = 7;
const HEAD_FOLLOW_YAW = 0.45;
const HEAD_FOLLOW_PITCH = 0.35;
const SACCADE_REACH = 0.03;

export const GAZE_TARGETS = {
  camera: [0, 0],
  left: [-0.8, 0],
  right: [0.8, 0],
  up: [0, 0.5],
  down: [0, -0.5],
  away: [0.7, 0.3],
};

export class Gaze {
  constructor(target, origin) {
    this.target = target;
    this.origin = origin;
    this.goal = GAZE_TARGETS.camera;
    this.saccade = [0, 0];
    this.nextSaccadeTime = 0;
    this.position = [0, 0];
  }

  look(name) {
    if (!Object.hasOwn(GAZE_TARGETS, name))
      throw new Error(`Unknown gaze target: ${name}`);
    this.goal = GAZE_TARGETS[name];
  }

  update(timestamp, delta, random = Math.random) {
    if (timestamp >= this.nextSaccadeTime) {
      this.saccade = [
        (random() - 0.5) * SACCADE_REACH,
        (random() - 0.5) * SACCADE_REACH,
      ];
      this.nextSaccadeTime = timestamp + 900 + random() * 2600;
    }
    const share = 1 - Math.exp(-GAZE_FOLLOW_RATE * delta);
    this.position = this.position.map(
      (value, axis) =>
        value + (this.goal[axis] + this.saccade[axis] - value) * share,
    );
    this.target.position.set(
      this.origin.x + this.position[0],
      this.origin.y + this.position[1],
      this.origin.z,
    );
  }

  headTurn() {
    return {
      yaw: this.position[0] * HEAD_FOLLOW_YAW,
      pitch: this.position[1] * HEAD_FOLLOW_PITCH,
    };
  }
}
