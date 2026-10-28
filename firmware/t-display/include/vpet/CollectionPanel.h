#pragma once

#include "vpet/CollectionStore.h"
#include "vpet/Input.h"
#include "vpet/LearningRuntime.h"

class TFT_eSprite;

namespace vpet {
class AssetStore;

// Optional injected controller keeps collection storage and its independent TFT
// surface out of the legacy Panels/Status renderer and legacy host harnesses.
class CollectionPanel {
public:
    using SeedGenerator = uint32_t (*)();
    enum class Page : uint8_t {
        Migration, List, Detail, Parents, ConfirmMigration, ConfirmFounder,
        ConfirmSwitch, ConfirmBreed, ConfirmDiscard, Error, Preferences
    };
    CollectionPanel(CollectionStore& store, SettingsStore& legacy, ProfileGenerator profiles,
                    SeedGenerator seeds, TFT_eSprite* canvas = nullptr, AssetStore* assets = nullptr,
                    LearningRuntime* learning = nullptr);
    virtual ~CollectionPanel() = default;
    virtual CollectionLoad load(PetState& pet, Settings& settings);
    virtual bool save(const PetState& pet, const Settings& settings);
    virtual bool saveCare(const PetState& pet, const Settings& settings);
    virtual bool settleCare();
    virtual bool recoverCare(const PetState& pet, const Settings& settings);
    bool compactCare() const { return store_.compactCare(); }
    virtual bool saveExperience(const PetState& pet, const Settings& settings,
                                const RuntimeExperience* events, size_t count);
    virtual int chooseAuto(const practice::Fighter& fighter, uint8_t learnedMask) const;
    virtual bool advance(uint32_t elapsedMs, bool paused);
    // RAM only: feeding must not run a filesystem checkpoint before first draw.
    virtual bool accumulate(uint32_t elapsedMs, bool paused);
    virtual bool hatchReady() const;
    virtual bool timedEgg() const;
    virtual void open();
    void setPreview(const PetState& pet) { previewForm_=static_cast<uint8_t>(pet.species()); }
    // True means close; changedActive asks App to rebase all runtime clocks.
    virtual bool input(InputEvent event, PetState& pet, Settings& settings,
                       const CollectionSwitchGuard& guard);
    virtual void draw(const char* language);
    bool enabled() const { return enabled_; }
    bool failed() const { return failed_ || careFailed_; }
    bool changedActive() const { return changedActive_; }
    Page page() const { return page_; }
    const CollectionState& state() const { return state_; }

private:
    enum class BlockReason : uint8_t { None, Sleeping, Paused, Exploring, Training,
        Battle, Action, PendingSave, Storage };
    bool flush();
    bool migrate(PetState& pet, Settings& settings);
    bool founder(const PetState& pet, const Settings& settings);
    bool eligible(const PetState& pet, size_t a, size_t b);
    bool breed(const PetState& pet, const Settings& settings);
    void error(const char* message, bool storage = false);
    void beginParents(const PetState& pet, uint8_t first=255);
    void refreshParents(const PetState& pet);
    void text(int x, int y, const char* label, uint16_t color, int font=1);
    void centered(int x, int y, const char* label, uint16_t color);
    void button(int x, int width, uint8_t index, const char* icon, const char* label="");
    void icon(const char* name, int x, int y, int size=16);
    void portraitForm(uint8_t form, int x, int y, int size, bool flip=false, bool muted=false);
    void portrait(uint8_t slot, int x, int y, int size, bool flip=false, bool muted=false);
    CollectionStore& store_;
    SettingsStore& legacy_;
    ProfileGenerator profiles_;
    SeedGenerator seeds_;
    TFT_eSprite* canvas_;
    AssetStore* assets_;
    LearningRuntime* learning_;
    CollectionState state_;
    Page page_ = Page::Migration;
    uint8_t cursor_ = 0, selected_ = 0, parentA_ = 255;
    uint8_t parentMask_ = 0, previewForm_ = 3;
    BlockReason blockReason_ = BlockReason::None;
    uint32_t pendingElapsed_ = 0;
    bool enabled_ = false, failed_ = false, changedActive_ = false;
    bool careFailed_ = false, careUnsettled_ = false;
    const char* message_ = "";
};
}  // namespace vpet
