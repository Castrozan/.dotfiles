const POSE_BLEND_RATE = 5;
const ARMS_DOWN = {
  leftUpperArm: [0, 0, 1.2],
  rightUpperArm: [0, 0, -1.2],
  leftLowerArm: [0, 0, 0.12],
  rightLowerArm: [0, 0, -0.12],
};

export const POSES = {
  relaxed: ARMS_DOWN,
  attentive: { ...ARMS_DOWN, spine: [-0.06, 0, 0], neck: [0.04, 0, 0] },
  confident: {
    leftUpperArm: [0, 0.35, 0.95],
    rightUpperArm: [0, -0.35, -0.95],
    leftLowerArm: [0, 1.6, 0],
    rightLowerArm: [0, -1.6, 0],
    spine: [0.03, 0, 0],
  },
  "lean-left": { ...ARMS_DOWN, spine: [0, 0, 0.07], neck: [0, 0, -0.04] },
  "lean-right": { ...ARMS_DOWN, spine: [0, 0, -0.07], neck: [0, 0, 0.04] },
  thoughtful: {
    ...ARMS_DOWN,
    rightUpperArm: [0, 0.8, -0.55],
    rightLowerArm: [0, 2.3, 0],
    rightHand: [0, 0, 0.35],
    head: [-0.04, 0, -0.08],
  },
};

const easeInOut = (phase) => Math.sin(Math.PI * phase);

export const GESTURES = {
  wave: {
    seconds: 2.4,
    motion: (phase) => {
      const raised = Math.min(1, easeInOut(phase) * 1.8);
      const swing = Math.sin(phase * Math.PI * 8) * 0.3;
      return {
        rightUpperArm: [0, raised * 0.85, raised * 1.05],
        rightLowerArm: [0, 0, raised * (1.9 + swing)],
        head: [0, 0, raised * 0.05],
      };
    },
  },
  nod: {
    seconds: 1.1,
    motion: (phase) => ({
      head: [-Math.abs(Math.sin(phase * Math.PI * 2)) * 0.2, 0, 0],
    }),
  },
  shake: {
    seconds: 1.3,
    motion: (phase) => ({
      head: [0, Math.sin(phase * Math.PI * 4) * easeInOut(phase) * 0.28, 0],
    }),
  },
  tilt: {
    seconds: 1.6,
    motion: (phase) => ({ head: [0, 0, easeInOut(phase) * 0.2] }),
  },
  bow: {
    seconds: 2,
    motion: (phase) => ({
      spine: [-easeInOut(phase) * 0.4, 0, 0],
      neck: [-easeInOut(phase) * 0.15, 0, 0],
    }),
  },
  shrug: {
    seconds: 1.6,
    motion: (phase) => {
      const lift = easeInOut(phase);
      return {
        leftShoulder: [0, 0, -lift * 0.2],
        rightShoulder: [0, 0, lift * 0.2],
        leftUpperArm: [0, 0, -lift * 0.25],
        rightUpperArm: [0, 0, lift * 0.25],
        leftLowerArm: [0, -lift * 1.3, 0],
        rightLowerArm: [0, lift * 1.3, 0],
        head: [0, 0, lift * 0.08],
      };
    },
  },
  cheer: {
    seconds: 2,
    motion: (phase) => {
      const raised = Math.min(1, easeInOut(phase) * 1.6);
      const bounce = Math.sin(phase * Math.PI * 6) * 0.15;
      return {
        leftUpperArm: [0, 0, -raised * (1.9 + bounce)],
        rightUpperArm: [0, 0, raised * (1.9 + bounce)],
        leftLowerArm: [0, 0, -raised * 0.2],
        rightLowerArm: [0, 0, raised * 0.2],
      };
    },
  },
  point: {
    seconds: 2,
    motion: (phase) => {
      const raised = Math.min(1, easeInOut(phase) * 1.8);
      return {
        rightUpperArm: [0, raised * 1.1, raised * 1.15],
        rightLowerArm: [0, raised * 0.25, 0],
      };
    },
  },
};

const IDLE_DEPTH = { still: 0, breathing: 1, floating: 1, lively: 2.4 };

function addAngles(angles, additions) {
  for (const [bone, [x, y, z]] of Object.entries(additions)) {
    const angle = angles[bone] ?? [0, 0, 0];
    angles[bone] = [angle[0] + x, angle[1] + y, angle[2] + z];
  }
}

function idleMotion(timestamp, depth) {
  const seconds = timestamp / 1000;
  return {
    chest: [Math.sin(seconds * 1.6) * 0.012 * depth, 0, 0],
    spine: [0, 0, Math.sin(seconds * 0.5) * 0.012 * depth],
    head: [
      Math.sin(seconds * 0.6) * 0.02 * depth,
      Math.sin(seconds * 0.43) * 0.05 * depth,
      Math.sin(seconds * 0.31) * 0.015 * depth,
    ],
  };
}

export class BodyPerformance {
  constructor(boneByName) {
    this.boneByName = boneByName;
    this.pose = POSES.relaxed;
    this.gesture = null;
    this.blended = Object.fromEntries(
      Object.entries(POSES.relaxed).map(([bone, angle]) => [bone, [...angle]]),
    );
  }

  setPose(name) {
    if (!Object.hasOwn(POSES, name)) throw new Error(`Unknown pose: ${name}`);
    this.pose = POSES[name];
  }

  playGesture(name, timestamp) {
    if (!Object.hasOwn(GESTURES, name))
      throw new Error(`Unknown gesture: ${name}`);
    this.gesture = { ...GESTURES[name], startedAt: timestamp };
  }

  blendTowardPose(delta) {
    const share = 1 - Math.exp(-POSE_BLEND_RATE * delta);
    for (const bone of new Set([
      ...Object.keys(this.blended),
      ...Object.keys(this.pose),
    ])) {
      const current = this.blended[bone] ?? [0, 0, 0];
      const target = this.pose[bone] ?? [0, 0, 0];
      this.blended[bone] = current.map(
        (angle, axis) => angle + (target[axis] - angle) * share,
      );
    }
  }

  gestureMotion(timestamp) {
    if (!this.gesture) return {};
    const phase = (timestamp - this.gesture.startedAt) / 1000 / this.gesture.seconds;
    if (phase >= 1) {
      this.gesture = null;
      return {};
    }
    return this.gesture.motion(phase);
  }

  update(timestamp, delta, { idleMode, mouth, headTurn }) {
    this.blendTowardPose(delta);
    const angles = {};
    addAngles(angles, this.blended);
    addAngles(angles, idleMotion(timestamp, IDLE_DEPTH[idleMode] ?? 0));
    addAngles(angles, { head: [-mouth * 0.04 + headTurn.pitch, headTurn.yaw, 0] });
    addAngles(angles, this.gestureMotion(timestamp));
    for (const [bone, angle] of Object.entries(angles))
      this.boneByName(bone)?.rotation.set(...angle);
  }
}

export function idleModes() {
  return Object.keys(IDLE_DEPTH);
}
