export class Element {
  constructor(identifier = null) {
    this.attributes = new Set();
    this.children = [];
    this.parent = null;
    this.isConnected = true;
    if (identifier) this.replaceChannel(identifier);
  }
  replaceChannel(identifier) {
    this.card = true;
    this.data = {
      content: {
        lockupViewModel: {
          contentType: "LOCKUP_CONTENT_TYPE_VIDEO",
          metadata: {
            lockupMetadataViewModel: {
              image: {
                decoratedAvatarViewModel: {
                  rendererContext: {
                    commandContext: {
                      onTap: {
                        innertubeCommand: {
                          browseEndpoint: { browseId: identifier },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
    };
  }
  append(child) {
    this.children.push(child);
    child.parent = this;
  }
  contains(child) {
    return this.children.includes(child);
  }
  matches() {
    return Boolean(this.card);
  }
  closest() {
    return this.card ? this : this.parent?.closest();
  }
  querySelectorAll() {
    return this.children.filter((child) => child.card);
  }
  removeAttribute(name) {
    this.attributes.delete(name);
  }
  hasAttribute(name) {
    return this.attributes.has(name);
  }
  toggleAttribute(name, enabled) {
    if (enabled) this.attributes.add(name);
    else this.attributes.delete(name);
  }
}
